from collections import OrderedDict

from domain.models.stage_path import StagePath
from domain.models.stages import AbstractStage, BuildStage, ExecuteStage, TestStage
from domain.models.student_stage_path_result import StudentStagePathResult
from domain.models.student_stage_result import AbstractStudentStageResult, \
    BuildSuccessStudentStageResult, ExecuteSuccessStudentStageResult, TestSuccessStudentStageResult
from domain.models.values import StudentID
from infra.repositories.student_stage_result import StudentStageResultRepository
from services.student_submission import StudentSubmissionGetChecksumService
from services.testcase_config import TestCaseConfigGetExecuteConfigMtimeService, \
    TestCaseConfigGetTestConfigMtimeService


class StudentStagePathResultGetService:
    # 生徒の指定されたステージパスの各ステージの結果を取得する
    # テーブル表示におけるHOTSPOT

    def __init__(
            self,
            *,
            student_stage_result_repo: StudentStageResultRepository,
    ):
        self._student_stage_result_repo = student_stage_result_repo

    def execute(self, student_id: StudentID, stage_path: StagePath) \
            -> StudentStagePathResult | None:
        stage_results: OrderedDict[AbstractStage, AbstractStudentStageResult | None] = OrderedDict()
        for stage in stage_path:
            is_finished = self._student_stage_result_repo.exists(
                student_id=student_id,
                stage=stage,
            )
            if not is_finished:
                stage_result = None
            else:
                stage_result = self._student_stage_result_repo.get(
                    student_id=student_id,
                    stage=stage,
                )
            stage_results[stage] = stage_result
        return StudentStagePathResult(
            stage_results=stage_results,
        )


# TODO: StagePathResultが一つの集約じゃね？？？？
# class StudentStagePathResultQueryService:
#     def __init__(
#             self,
#             *,
#             project_database_io: ProjectDatabaseIO,
#     ):
#         self._project_database_io = project_database_io
#
#     def execute(self, student_id: StudentID, stage_path: StagePath) \
#             -> StudentStagePathResult | None:
#         stage_results: OrderedDict[AbstractStage, AbstractStudentStageResult | None] = OrderedDict()
#         with self._project_database_io.connect() as con:
#             con.execute(
#                 """
#                 SELECT *
#                 FROM student_build_result AS build
#
#                 """
#             )


class StudentStagePathResultCheckRollbackService:
    def __init__(
            self,
            student_submission_get_checksum_service: StudentSubmissionGetChecksumService,
            testcase_config_get_execute_config_mtime_service: TestCaseConfigGetExecuteConfigMtimeService,
            testcase_config_get_test_config_mtime_service: TestCaseConfigGetTestConfigMtimeService,
    ):
        self._student_submission_get_checksum_service \
            = student_submission_get_checksum_service
        self._testcase_config_get_execute_config_mtime_service \
            = testcase_config_get_execute_config_mtime_service
        self._testcase_config_get_test_config_mtime_service \
            = testcase_config_get_test_config_mtime_service

    def execute(
            self,
            *,
            stage_path_result: StudentStagePathResult,
            student_id: StudentID,
    ) -> type[AbstractStage] | None:  # ロールバック先のステージを返し，ロールバックしない場合はNone
        # * BUILDステージが成功しているとき
        result = stage_path_result.get_result_by_stage_type(BuildStage)
        if result is not None and result.is_success:
            assert isinstance(result, BuildSuccessStudentStageResult)
            # 現在のチェックサムがステージ実行時の生徒の提出フォルダのチェックサムと異なればロールバック
            checksum = self._student_submission_get_checksum_service.execute(
                student_id=student_id,
            )
            if checksum != result.submission_folder_checksum:
                return BuildStage

        # * EXECUTEステージが成功しているとき
        # noinspection DuplicatedCode
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
                return ExecuteStage

        # * TESTステージが成功しているとき
        # noinspection DuplicatedCode
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
                return TestStage

        # ロールバックしてない
        return None
