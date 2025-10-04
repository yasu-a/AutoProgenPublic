from datetime import datetime

from domain.model.stage_path import StagePath
from domain.model.stage import AbstractStage, BuildStage, ExecuteStage, TestStage
from domain.model.student_stage_path_result import StudentStagePathResult
from domain.model.student_stage_result import BuildSuccessStudentStageResult, \
    ExecuteSuccessStudentStageResult, TestSuccessStudentStageResult, AbstractStudentStageResult
from domain.model.value import StudentID
from infra.repository.student_stage_path_result import StudentStagePathResultRepository
from service.stage_path import StagePathListSubService
from service.student_submission import StudentSubmissionGetChecksumService
from service.testcase_config import TestCaseConfigGetExecuteConfigMtimeService, \
    TestCaseConfigGetTestConfigMtimeService


class StudentStagePathResultGetService:
    # 生徒の指定されたステージパスの各ステージの結果を取得する
    # テーブル表示におけるHOTSPOT

    def __init__(
            self,
            *,
            student_stage_path_result_repo: StudentStagePathResultRepository,
    ):
        self._student_stage_path_result_repo = student_stage_path_result_repo

    def execute(self, student_id: StudentID, stage_path: StagePath) \
            -> StudentStagePathResult | None:
        return self._student_stage_path_result_repo.get(student_id, stage_path)


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
            stage = result.stage
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
            # 現在のテスト構成の更新時刻がステージ実行時のテスト構成の更新時刻と異なればロールバック
            stage = result.stage
            assert isinstance(stage, TestStage)
            mtime = self._testcase_config_get_test_config_mtime_service.execute(
                testcase_id=stage.testcase_id,
            )
            if mtime != result.test_config_mtime:
                return TestStage

        return None


class StudentStageResultCheckTimestampQueryService:
    # 生徒の進捗データの最終更新日時を取得する

    def __init__(
            self,
            *,
            student_stage_path_result_repo: StudentStagePathResultRepository,
    ):
        self._student_stage_path_result_repo = student_stage_path_result_repo

    def execute(self, student_id: StudentID) -> datetime | None:  # None if no file exists
        return self._student_stage_path_result_repo.get_timestamp(student_id)


class StudentStageResultRollbackService:
    # 与えられたステージ以降（与えられたステージ自身を含む）の結果生成をなかったことにする

    def __init__(
            self,
            *,
            student_stage_path_result_repo: StudentStagePathResultRepository,
    ):
        self._student_stage_path_result_repo = student_stage_path_result_repo

    def execute(
            self,
            *,
            student_id: StudentID,
            stage_path: StagePath,
            stage_type: type[AbstractStage],
    ) -> None:
        stage_path_result = self._student_stage_path_result_repo.get(student_id, stage_path)
        for stage in reversed(stage_path):
            stage_path_result.delete_result(stage)
            if isinstance(stage, stage_type):
                break
        self._student_stage_path_result_repo.put(stage_path_result)


class StudentStageResultClearService:
    # 生徒の結果データを全削除する

    def __init__(
            self,
            *,
            stage_path_list_sub_service: StagePathListSubService,
            student_stage_path_result_repo: StudentStagePathResultRepository,
    ):
        self._stage_path_list_sub_service = stage_path_list_sub_service
        self._student_stage_path_result_repo = student_stage_path_result_repo

    def execute(
            self,
            *,
            student_id: StudentID,
    ) -> None:
        stage_paths = self._stage_path_list_sub_service.execute()
        for stage_path in stage_paths:
            stage_path_result = self._student_stage_path_result_repo.get(student_id, stage_path)
            stage_path_result.delete_all_results()
            self._student_stage_path_result_repo.put(stage_path_result)


class StudentPutStageResultService:
    def __init__(
            self,
            *,
            student_stage_path_result_repo: StudentStagePathResultRepository,
    ):
        self._student_stage_path_result_repo = student_stage_path_result_repo

    def execute(self, stage_path: StagePath, result: AbstractStudentStageResult) -> None:
        stage_path_result = self._student_stage_path_result_repo.get(
            student_id=result.student_id,
            stage_path=stage_path,
        )
        stage_path_result.put_result(result)
        self._student_stage_path_result_repo.put(stage_path_result)


class StudentGetStageResultService:
    def __init__(
            self,
            *,
            student_stage_path_result_repo: StudentStagePathResultRepository,
    ):
        self._student_stage_path_result_repo = student_stage_path_result_repo

    def execute(self, student_id: StudentID, stage_path: StagePath,
                stage: AbstractStage) -> AbstractStudentStageResult:
        stage_path_result = self._student_stage_path_result_repo.get(
            student_id=student_id,
            stage_path=stage_path,
        )
        return stage_path_result.get_result(stage)
