from typing import Callable

from domain.error import StopTask
from domain.model.stage_path import StagePath
from domain.model.stage import AbstractStage, BuildStage, CompileStage, ExecuteStage, TestStage
from domain.model.student_stage_path_result import StudentStagePathResult
from domain.model.value import StudentID
from infra.repository.student_stage_path_result import StudentStagePathResultRepository
from service.stage_path import StagePathListSubService
from service.student_stage_path_result import StudentStagePathResultGetService, \
    StudentStagePathResultCheckRollbackService
from usecase.student_run_build import StudentRunBuildStageUseCase
from usecase.student_run_compile import StudentRunCompileStageUseCase
from usecase.student_run_execute import StudentRunExecuteStageUseCase
from usecase.student_run_test import StudentRunTestStageUseCase
from util.app_logging import create_logger


class StudentRunNextStageUseCase:
    _logger = create_logger()

    def __init__(
            self,
            stage_path_list_sub_service: StagePathListSubService,
            student_stage_path_result_get_service: StudentStagePathResultGetService,
            student_stage_path_result_repo: StudentStagePathResultRepository,
            student_run_build_stage_usecase: StudentRunBuildStageUseCase,  # usecase dependency
            student_run_compile_stage_usecase: StudentRunCompileStageUseCase,
            student_run_execute_stage_usecase: StudentRunExecuteStageUseCase,
            student_run_test_stage_usecase: StudentRunTestStageUseCase,
            student_stage_path_result_check_rollback_service: StudentStagePathResultCheckRollbackService,
    ):
        self._stage_path_list_sub_service \
            = stage_path_list_sub_service
        self._student_stage_path_result_get_service \
            = student_stage_path_result_get_service
        self._student_stage_path_result_repo \
            = student_stage_path_result_repo
        self._student_run_build_stage_usecase \
            = student_run_build_stage_usecase
        self._student_run_compile_stage_usecase \
            = student_run_compile_stage_usecase
        self._student_run_execute_stage_usecase \
            = student_run_execute_stage_usecase
        self._student_run_test_stage_usecase \
            = student_run_test_stage_usecase
        self._student_stage_path_result_check_rollback_service \
            = student_stage_path_result_check_rollback_service

    def __rollback(
            self,
            *,
            student_id: StudentID,
            stage_path_result: StudentStagePathResult,
            stage_paths: list[StagePath],
    ) -> bool:
        # ロールバックが必要かを判定する
        rollback_stage_type = self._student_stage_path_result_check_rollback_service.execute(
            student_id=student_id,
            stage_path_result=stage_path_result,
        )
        # ロールバック不要なら何もしない
        if rollback_stage_type is None:
            return False

        # 共有ステージは全テストケースに適用する
        if rollback_stage_type in (BuildStage, CompileStage):
            targets = stage_paths
        else:
            # 個別ステージは現在のテストケースだけに適用する
            targets = [stage_path_result.stage_path]

        # 対象ステージ以降の結果を削除して保存し直す
        for target_stage_path in targets:
            target_stage_path_result = self._student_stage_path_result_repo.get(
                student_id,
                target_stage_path,
            )
            for stage in reversed(target_stage_path):
                target_stage_path_result.delete_result(stage)
                if isinstance(stage, rollback_stage_type):
                    break
            self._student_stage_path_result_repo.put(target_stage_path_result)
        # 適用内容をログに残す
        self._logger.info(f"{student_id} rollback {rollback_stage_type} on {len(targets)} path(s)")
        return True

    @staticmethod
    def __select_next_stage_target(
            stage_path_results: list[tuple[int, StudentStagePathResult]],
            skipped_stage_path_indexes: set[int],
    ) -> tuple[int, AbstractStage] | None:
        # ステージ優先順で次に実行する対象を1つ選ぶ
        for stage_type in (BuildStage, CompileStage, ExecuteStage, TestStage):
            for stage_path_index, stage_path_result in stage_path_results:
                # このステップで進捗なしと判定済みのパスは除外する
                if stage_path_index in skipped_stage_path_indexes:
                    continue
                # そのパスで次に実行すべきステージを調べる
                next_stage = stage_path_result.get_next_stage()
                # 優先中のステージ型なら実行対象に採用する
                if isinstance(next_stage, stage_type):
                    return stage_path_index, next_stage
        # 実行できるものがなければ終了する
        return None

    def __get_stage_path_results(
            self,
            *,
            student_id: StudentID,
            stage_paths: list[StagePath],
    ) -> list[StudentStagePathResult]:
        # 各ステージパスの最新結果をまとめて取得する
        return [
            self._student_stage_path_result_get_service.execute(student_id, stage_path)
            for stage_path in stage_paths
        ]

    def __apply_all_rollbacks(
            self,
            *,
            student_id: StudentID,
            stage_paths: list[StagePath],
    ) -> bool:
        # 全ステージパスに対して必要なロールバックを先に片付ける
        any_rollback_applied = False
        stage_path_results = self.__get_stage_path_results(
            student_id=student_id,
            stage_paths=stage_paths,
        )
        for stage_path_result in stage_path_results:
            # 1パスずつロールバック要否を確認して適用する
            rollback_applied = self.__rollback(
                student_id=student_id,
                stage_path_result=stage_path_result,
                stage_paths=stage_paths,
            )
            # 何か1件でもロールバックしたら再評価が必要
            if rollback_applied:
                any_rollback_applied = True
        return any_rollback_applied

    def __execute_single_stage(
            self,
            *,
            student_id: StudentID,
            stage_path: StagePath,
            next_stage: AbstractStage,
    ) -> None:
        # BUILDステージを実行する
        if isinstance(next_stage, BuildStage):
            self._logger.info(f"{student_id} run BUILD {next_stage}")
            self._student_run_build_stage_usecase.execute(
                student_id=student_id,
                stage_path=stage_path,
            )
        # COMPILEステージを実行する
        elif isinstance(next_stage, CompileStage):
            self._logger.info(f"{student_id} run COMPILE {next_stage}")
            self._student_run_compile_stage_usecase.execute(
                student_id=student_id,
                stage_path=stage_path,
            )
        # EXECUTEステージを実行する
        elif isinstance(next_stage, ExecuteStage):
            self._logger.info(f"{student_id} run EXECUTE {next_stage}")
            self._student_run_execute_stage_usecase.execute(
                student_id=student_id,
                stage_path=stage_path,
            )
        # TESTステージを実行する
        elif isinstance(next_stage, TestStage):
            self._logger.info(f"{student_id} run TEST {next_stage}")
            self._student_run_test_stage_usecase.execute(
                student_id=student_id,
                stage_path=stage_path,
            )
        # 想定外のステージ型は異常とする
        else:
            assert False, next_stage

    def __step(
            self,
            *,
            student_id: StudentID,
            stage_paths: list[StagePath],
            skipped_stage_path_indexes: set[int],
    ) -> tuple[bool, int | None]:
        # まずロールバックをすべて処理して状態を正規化する
        if self.__apply_all_rollbacks(
                student_id=student_id,
                stage_paths=stage_paths,
        ):
            return True, None

        # ロールバック後の最新状態を取得する
        stage_path_results = self.__get_stage_path_results(
            student_id=student_id,
            stage_paths=stage_paths,
        )
        selectable_stage_path_results = list(enumerate(stage_path_results))

        # 1件だけ実行候補を選んで試す
        selected = self.__select_next_stage_target(
            stage_path_results=selectable_stage_path_results,
            skipped_stage_path_indexes=skipped_stage_path_indexes,
        )
        if selected is None:
            return False, None

        stage_path_index, next_stage = selected
        stage_path = stage_paths[stage_path_index]
        stage_path_result_before = stage_path_results[stage_path_index]
        finish_states_before_run = stage_path_result_before.stage_statuses

        self.__execute_single_stage(
            student_id=student_id,
            stage_path=stage_path,
            next_stage=next_stage,
        )

        finish_states_after_run = self._student_stage_path_result_get_service.execute(
            student_id,
            stage_path,
        ).stage_statuses
        if finish_states_before_run != finish_states_after_run:
            return True, None
        return False, stage_path_index

    def execute(
            self,
            *,
            student_id: StudentID,
            stop_producer: Callable[[], bool],  # 停止するときTrueを受け取る
    ) -> None:
        # 現在のテストケース構成からステージパスを1回だけ取得する
        stage_path_lst: list[StagePath] = self._stage_path_list_sub_service.execute()
        # 1ステップずつ進め，進捗がなくなったら終了する
        while True:
            # 停止要求があれば中断する
            if stop_producer():
                raise StopTask()

            skipped_stage_path_indexes: set[int] = set()
            while True:
                progressed, skipped_stage_path_index = self.__step(
                    student_id=student_id,
                    stage_paths=stage_path_lst,
                    skipped_stage_path_indexes=skipped_stage_path_indexes,
                )
                if progressed:
                    break
                if skipped_stage_path_index is None:
                    break
                skipped_stage_path_indexes.add(skipped_stage_path_index)

            if not progressed:
                break
