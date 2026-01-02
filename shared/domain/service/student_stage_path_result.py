from datetime import datetime

from shared.domain.entity.student_stage_path_result import StudentStagePathResultEntity
from shared.domain.interface.gateway import IStudentSubmissionGetChecksumGateway
from shared.domain.service.stage_path import StagePathListSubService
from shared.domain.value.identifier import StudentID
from shared.domain.value.stage import AbstractStage, BuildStage, ExecuteStage, TestStage
from shared.domain.value.stage_path import StagePath
from shared.domain.value.student_stage_result import BuildSuccessStudentStageResult, \
    ExecuteSuccessStudentStageResult, TestSuccessStudentStageResult, AbstractStudentStageResult
from shared.infra.repository.student_stage_path_result import StudentStagePathResultEntityRepository
from shared.infra.repository.testcase_config import TestCaseConfigRepository


class StudentStagePathResultEntityCheckRollbackService:
    def __init__(
            self,
            student_submission_get_checksum_gateway: IStudentSubmissionGetChecksumGateway,
            testcase_config_repo: TestCaseConfigRepository,
    ):
        self._student_submission_get_checksum_gateway \
            = student_submission_get_checksum_gateway
        self._testcase_config_repo = testcase_config_repo

    def execute(
            self,
            *,
            stage_path_result: StudentStagePathResultEntity,
            student_id: StudentID,
    ) -> type[AbstractStage] | None:  # ロールバック先のステージを返し，ロールバックしない場合はNone
        # * BUILDステージが成功しているとき
        result = stage_path_result.get_result_by_stage_type(BuildStage)
        if result is not None and result.is_success:
            assert isinstance(result, BuildSuccessStudentStageResult)
            # 現在のチェックサムがステージ実行時の生徒の提出フォルダのチェックサムと異なればロールバック
            checksum = self._student_submission_get_checksum_gateway.execute(
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
            mtime = self._testcase_config_repo.get(
                stage.testcase_id).execute_config.mtime
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
            mtime = self._testcase_config_repo.get(
                stage.testcase_id).test_config.mtime
            if mtime != result.test_config_mtime:
                return TestStage

        return None


class StudentStagePathResultEntityRollbackService:
    # 与えられたステージ以降（与えられたステージ自身を含む）の結果生成をなかったことにする

    def __init__(
            self,
            *,
            student_stage_path_result_repo: StudentStagePathResultEntityRepository,
    ):
        self._student_stage_path_result_repo = student_stage_path_result_repo

    def execute(
            self,
            *,
            student_id: StudentID,
            stage_path: StagePath,
            stage_type: type[AbstractStage],
    ) -> None:
        stage_path_result = self._student_stage_path_result_repo.get(
            student_id, stage_path)
        for stage in reversed(stage_path):
            stage_path_result.delete_result(stage)
            if isinstance(stage, stage_type):
                break
        self._student_stage_path_result_repo.put(stage_path_result)


class StudentStagePathResultEntityClearService:
    # 生徒の結果データを全削除する

    def __init__(
            self,
            *,
            stage_path_list_sub_service: StagePathListSubService,
            student_stage_path_result_repo: StudentStagePathResultEntityRepository,
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
            stage_path_result = self._student_stage_path_result_repo.get(
                student_id, stage_path)
            stage_path_result.delete_all_results()
            self._student_stage_path_result_repo.put(stage_path_result)


class StudentPutStagePathResultEntityService:
    def __init__(
            self,
            *,
            student_stage_path_result_repo: StudentStagePathResultEntityRepository,
    ):
        self._student_stage_path_result_repo = student_stage_path_result_repo

    def execute(self, stage_path: StagePath, result: AbstractStudentStageResult) -> None:
        stage_path_result = self._student_stage_path_result_repo.get(
            student_id=result.student_id,
            stage_path=stage_path,
        )
        stage_path_result.put_result(result)
        self._student_stage_path_result_repo.put(stage_path_result)


class StudentGetStagePathResultEntityService:
    def __init__(
            self,
            *,
            student_stage_path_result_repo: StudentStagePathResultEntityRepository,
    ):
        self._student_stage_path_result_repo = student_stage_path_result_repo

    def execute(
            self,
            student_id: StudentID,
            stage_path: StagePath,
    ) -> StudentStagePathResultEntity:
        return self._student_stage_path_result_repo.get(student_id, stage_path)


class StudentStagePathResultEntityCheckTimestampQueryService:
    def __init__(
            self,
            *,
            student_stage_path_result_repo: StudentStagePathResultEntityRepository,
    ):
        self._student_stage_path_result_repo = student_stage_path_result_repo

    def execute(self, student_id: StudentID) -> datetime | None:
        return self._student_stage_path_result_repo.get_timestamp(student_id)
