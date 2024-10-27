from app_logging import create_logger
from domain.models.stages import BuildStage, CompileStage, ExecuteStage, TestStage
from domain.models.student_stage_path_result import StudentStagePathResult
from domain.models.student_stage_result import BuildSuccessStudentStageResult, \
    ExecuteSuccessStudentStageResult, TestSuccessStudentStageResult
from domain.models.values import StudentID
from services.stage import StageListChildSubService
from services.stage_path import StagePathListSubService
from services.student_stage_path_result import StudentStagePathResultGetService
from services.student_stage_result import StudentStageResultRollbackService
from services.student_submission import StudentSubmissionGetChecksumService
from services.testcase_config import TestCaseConfigGetExecuteConfigMtimeService, \
    TestCaseConfigGetTestConfigMtimeService
from transaction import transactional_with
from usecases.student_run_build import StudentRunBuildStageUseCase
from usecases.student_run_compile import StudentRunCompileStageUseCase
from usecases.student_run_execute import StudentRunExecuteStageUseCase
from usecases.student_run_test import StudentRunTestStageUseCase


class StudentRunNextStageUseCase:
    _logger = create_logger()

    def __init__(
            self,
            stage_list_child_sub_service: StageListChildSubService,
            stage_path_list_sub_service: StagePathListSubService,
            student_stage_path_result_get_service: StudentStagePathResultGetService,
            student_submission_get_checksum_service: StudentSubmissionGetChecksumService,
            testcase_config_get_execute_config_mtime_service: TestCaseConfigGetExecuteConfigMtimeService,
            testcase_config_get_test_config_mtime_service: TestCaseConfigGetTestConfigMtimeService,
            student_stage_result_rollback_service: StudentStageResultRollbackService,
            student_run_build_stage_usecase: StudentRunBuildStageUseCase,  # usecase dependency
            student_run_compile_stage_usecase: StudentRunCompileStageUseCase,
            student_run_execute_stage_usecase: StudentRunExecuteStageUseCase,
            student_run_test_stage_usecase: StudentRunTestStageUseCase,
    ):
        self._stage_list_child_sub_service \
            = stage_list_child_sub_service
        self._stage_path_list_sub_service \
            = stage_path_list_sub_service
        self._student_stage_path_result_get_service \
            = student_stage_path_result_get_service
        self._student_submission_get_checksum_service \
            = student_submission_get_checksum_service
        self._testcase_config_get_execute_config_mtime_service \
            = testcase_config_get_execute_config_mtime_service
        self._testcase_config_get_test_config_mtime_service \
            = testcase_config_get_test_config_mtime_service
        self._student_stage_result_rollback_service \
            = student_stage_result_rollback_service
        self._student_run_build_stage_usecase \
            = student_run_build_stage_usecase
        self._student_run_compile_stage_usecase \
            = student_run_compile_stage_usecase
        self._student_run_execute_stage_usecase \
            = student_run_execute_stage_usecase
        self._student_run_test_stage_usecase \
            = student_run_test_stage_usecase

    def __rollback(
            self,
            *,
            stage_path_result: StudentStagePathResult,
            student_id: StudentID,
    ) -> bool:  # ロールバックをしたらTrue
        # 完了したステージを検証し，場合に応じてロールバック

        # * BUILDステージが成功しているとき
        result = stage_path_result.get_result_by_stage_type(BuildStage)
        if result is not None and result.is_success:
            assert isinstance(result, BuildSuccessStudentStageResult)
            # 現在のチェックサムがステージ実行時の生徒の提出フォルダのチェックサムと異なればロールバック
            checksum = self._student_submission_get_checksum_service.execute(
                student_id=student_id,
            )
            if checksum != result.submission_folder_checksum:
                self._student_stage_result_rollback_service.execute(
                    student_id=student_id,
                    stage_path=stage_path_result.get_stage_path(),
                    stage_type=BuildStage,
                )
                self._logger.info(f"{student_id} rollback BUILD")
                return True

        # * EXECUTEステージが成功しているとき
        result = stage_path_result.get_result_by_stage_type(ExecuteStage)
        if result is not None and result.is_success:
            assert isinstance(result, ExecuteSuccessStudentStageResult)
            # 現在の実行構成の更新時刻がステージ実行時の実行構成の更新時刻と異なればロールバック
            stage = stage_path_result.get_result_by_stage_type(ExecuteStage).stage
            assert isinstance(stage, ExecuteStage)
            mtime = self._testcase_config_get_execute_config_mtime_service.execute(
                testcase_id=stage.testcase_id,
            )
            if mtime != result.execute_config_mtime:
                self._student_stage_result_rollback_service.execute(
                    student_id=student_id,
                    stage_path=stage_path_result.get_stage_path(),
                    stage_type=ExecuteStage,
                )
                self._logger.info(f"{student_id} rollback EXECUTE")
                return True

        # * TESTステージが成功しているとき
        result = stage_path_result.get_result_by_stage_type(TestStage)
        if result is not None and result.is_success:
            assert isinstance(result, TestSuccessStudentStageResult)
            # 現在のテスト構成の更新時刻がステージ実行時の実行構成の更新時刻と異なればロールバック
            stage = stage_path_result.get_result_by_stage_type(TestStage).stage
            assert isinstance(stage, TestStage)
            mtime = self._testcase_config_get_test_config_mtime_service.execute(
                testcase_id=stage.testcase_id,
            )
            if mtime != result.test_config_mtime:
                self._student_stage_result_rollback_service.execute(
                    student_id=student_id,
                    stage_path=stage_path_result.get_stage_path(),
                    stage_type=TestStage,
                )
                self._logger.info(f"{student_id} rollback TEST")
                return True

        # ロールバックしてない
        return False

    @transactional_with("student_id")  # FIXME: ステージツリーもロックする必要がある
    def execute(self, student_id: StudentID) -> None:
        finished_stage_path_indexes = set()
        while True:
            stage_path_lst = self._stage_path_list_sub_service.execute()

            # 各ステージパスの実行可能なステージを1ステージだけ実行
            result_updated = False
            for stage_path_index, stage_path in enumerate(stage_path_lst):
                # このステージパスを実行してもこれ以上進捗がないことが判明しているなら即スキップ
                if stage_path_index in finished_stage_path_indexes:
                    continue

                # このステージパスの結果を取得
                stage_path_result: StudentStagePathResult \
                    = self._student_stage_path_result_get_service.execute(student_id, stage_path)

                # 完了したステージを検証し，場合に応じてロールバック
                is_rollback_dispatched = self.__rollback(
                    stage_path_result=stage_path_result,
                    student_id=student_id,
                )
                if is_rollback_dispatched:
                    # ロールバックが実行されたらもう一度このステージパスの結果を取得
                    stage_path_result: StudentStagePathResult \
                        = self._student_stage_path_result_get_service.execute(student_id,
                                                                              stage_path)

                # このステージパスのすべてのステージが終了しているなら終了
                if stage_path_result.are_all_stages_done():
                    finished_stage_path_indexes.add(stage_path_index)
                    continue

                # 次のステージを実行
                next_stage = stage_path_result.get_next_stage()
                if isinstance(next_stage, BuildStage):
                    self._logger.info(f"{student_id} run BUILD {next_stage}")
                    self._student_run_build_stage_usecase.execute(
                        student_id=student_id,
                    )
                elif isinstance(next_stage, CompileStage):
                    self._logger.info(f"{student_id} run COMPILE {next_stage}")
                    self._student_run_compile_stage_usecase.execute(
                        student_id=student_id,
                    )
                elif isinstance(next_stage, ExecuteStage):
                    self._logger.info(f"{student_id} run EXECUTE {next_stage}")
                    self._student_run_execute_stage_usecase.execute(
                        student_id=student_id,
                        testcase_id=next_stage.testcase_id,
                    )
                elif isinstance(next_stage, TestStage):
                    self._logger.info(f"{student_id} run TEST {next_stage}")
                    self._student_run_test_stage_usecase.execute(
                        student_id=student_id,
                        testcase_id=next_stage.testcase_id,
                    )
                else:
                    assert False, next_stage

                # 実行前の進捗の状況と実行後の進捗の状況を比較してこのステージパスの実行を終了するかどうかを決定
                finish_states_before_run = stage_path_result.get_finish_states()
                finish_states_after_run = (
                    self._student_stage_path_result_get_service.execute(
                        student_id,
                        stage_path,
                    ).get_finish_states()
                )
                if finish_states_before_run == finish_states_after_run:
                    finished_stage_path_indexes.add(stage_path_index)
                else:
                    result_updated = True

            # どのステージパスも進捗が無ければ終了
            if not result_updated:
                break
