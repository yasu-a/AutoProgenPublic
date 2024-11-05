from domain.models.stages import BuildStage, CompileStage, ExecuteStage, TestStage
from domain.models.student_stage_path_result import StudentStagePathResult
from domain.models.values import StudentID
from services.stage_path import StagePathListSubService
from services.student_stage_path_result import StudentStagePathResultGetService, \
    StudentStagePathResultCheckRollbackService
from services.student_stage_result import StudentStageResultRollbackService
from usecases.student_run_build import StudentRunBuildStageUseCase
from usecases.student_run_compile import StudentRunCompileStageUseCase
from usecases.student_run_execute import StudentRunExecuteStageUseCase
from usecases.student_run_test import StudentRunTestStageUseCase
from utils.app_logging import create_logger


class StudentRunNextStageUseCase:
    _logger = create_logger()

    def __init__(
            self,
            stage_path_list_sub_service: StagePathListSubService,
            student_stage_path_result_get_service: StudentStagePathResultGetService,
            student_stage_result_rollback_service: StudentStageResultRollbackService,
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
        self._student_stage_path_result_check_rollback_service \
            = student_stage_path_result_check_rollback_service

    def __rollback(
            self,
            *,
            stage_path_result: StudentStagePathResult,
            student_id: StudentID,
    ) -> bool:  # ロールバックをしたらTrue
        # 完了したステージを検証し，場合に応じてロールバック
        rollback_stage_type = self._student_stage_path_result_check_rollback_service.execute(
            student_id=student_id,
            stage_path_result=stage_path_result,
        )
        if rollback_stage_type is None:
            return False

        self._student_stage_result_rollback_service.execute(
            student_id=student_id,
            stage_path=stage_path_result.get_stage_path(),
            stage_type=rollback_stage_type,
        )
        self._logger.info(f"{student_id} rollback {rollback_stage_type}")
        return True

    def execute(self, student_id: StudentID) -> None:
        finished_stage_path_indexes = set()
        while True:
            stage_path_lst = self._stage_path_list_sub_service.execute()

            # 各ステージパスの実行可能なステージを1ステージだけ実行
            result_updated = False
            for stage_path_index, stage_path in enumerate(stage_path_lst):
                # このステージパスを実行してもこれ以上進捗がないことがすでに判明しているなら即スキップ
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
