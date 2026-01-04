from collections import OrderedDict
from datetime import datetime

from shared.domain.interface.gateway import IStudentSubmissionGetChecksumGateway
from shared.domain.interface.repository import IStudentStageResultRepository
from shared.domain.interface.service import IStudentGetStagePathResultMapService, \
    IStudentStagePathResultEntityCheckTimestampQueryService, \
    IStudentPutStagePathResultEntityService, IStudentStagePathResultEntityClearService, \
    IStudentStagePathResultEntityRollbackService, IStudentStagePathResultEntityCheckRollbackService, \
    IStagePathListSubService
from shared.domain.model.stage import StageElement, Stage
from shared.domain.model.student_result import AbstractStageResultEntity, \
    BuildStageResultEntity, ExecuteStageResultEntity, TestStageResultEntity
from shared.domain.value.identifier import StudentID
from shared.infra.repository.testcase_config import TestCaseConfigRepository


class StudentStagePathResultEntityCheckRollbackService(
    IStudentStagePathResultEntityCheckRollbackService,
):
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
            stage_path: list[StageElement],
            student_id: StudentID,
            results_map: OrderedDict[StageElement, AbstractStageResultEntity | None],
    ) -> Stage | None:  # ロールバック先のステージを返し，ロールバックしない場合はNone
        # * BUILDステージが成功しているとき
        result = next((r for e, r in results_map.items() if e.stage == Stage.BUILD), None)

        if result is not None and result.is_success:
            assert isinstance(result, BuildStageResultEntity)
            # 現在のチェックサムがステージ実行時の生徒の提出フォルダのチェックサムと異なればロールバック
            checksum = self._student_submission_get_checksum_gateway.execute(
                student_id=student_id,
            )
            if checksum != result.submission_folder_checksum:
                return Stage.BUILD

        # * EXECUTEステージが成功しているとき
        result = next((r for e, r in results_map.items() if e.stage == Stage.EXECUTE), None)

        if result is not None and result.is_success:
            assert isinstance(result, ExecuteStageResultEntity)
            # 現在の実行構成の更新時刻がステージ実行時の実行構成の更新時刻と異なればロールバック
            stage_element = next((e for e in results_map.keys() if e.stage == Stage.EXECUTE), None)
            assert stage_element is not None
            
            mtime = self._testcase_config_repo.get(
                stage_element.testcase_id).execute_config.mtime
            if mtime != result.execute_config_mtime:
                return Stage.EXECUTE

        # * TESTステージが成功しているとき
        result = next((r for e, r in results_map.items() if e.stage == Stage.TEST), None)
        
        if result is not None and result.is_success:
            assert isinstance(result, TestStageResultEntity)
            # 現在のテスト構成の更新時刻がステージ実行時のテスト構成の更新時刻と異なればロールバック
            stage_element = next((e for e in results_map.keys() if e.stage == Stage.TEST), None)
            assert stage_element is not None

            mtime = self._testcase_config_repo.get(
                stage_element.testcase_id).test_config.mtime
            if mtime != result.test_config_mtime:
                return Stage.TEST

        return None


class StudentStagePathResultEntityRollbackService(
    IStudentStagePathResultEntityRollbackService,
):
    # 与えられたステージ以降（与えられたステージ自身を含む）の結果生成をなかったことにする

    def __init__(
            self,
            *,
            student_stage_result_repo: IStudentStageResultRepository,
    ):
        self._student_stage_result_repo = student_stage_result_repo

    def execute(
            self,
            *,
            student_id: StudentID,
            stage_path: list[StageElement],
            stage_type: Stage,
    ) -> None:
        for stage_element in reversed(stage_path):
            self._student_stage_result_repo.delete(student_id, stage_element)
            if stage_element.stage == stage_type:
                break


class StudentStagePathResultEntityClearService(
    IStudentStagePathResultEntityClearService,
):
    # 生徒の結果データを全削除する

    def __init__(
            self,
            *,
            stage_path_list_sub_service: IStagePathListSubService,
            student_stage_result_repo: IStudentStageResultRepository,
    ):
        self._stage_path_list_sub_service = stage_path_list_sub_service
        self._student_stage_result_repo = student_stage_result_repo

    def execute(
            self,
            *,
            student_id: StudentID,
    ) -> None:
        stage_paths = self._stage_path_list_sub_service.execute()
        for stage_path in stage_paths:
            for stage_element in stage_path:
                self._student_stage_result_repo.delete(student_id, stage_element)


class StudentPutStagePathResultEntityService(
    IStudentPutStagePathResultEntityService,
):
    def __init__(
            self,
            *,
            student_stage_result_repo: IStudentStageResultRepository,
    ):
        self._student_stage_result_repo = student_stage_result_repo

    def execute(self, result: AbstractStageResultEntity) -> None:
        self._student_stage_result_repo.update(result)


class StudentGetStagePathResultMapService(IStudentGetStagePathResultMapService):
    def __init__(
            self,
            *,
            student_stage_result_repo: IStudentStageResultRepository,
    ):
        self._student_stage_result_repo = student_stage_result_repo

    def execute(
            self,
            student_id: StudentID,
            stage_path: list[StageElement],
    ) -> OrderedDict[StageElement, AbstractStageResultEntity | None]:
        stage_results: OrderedDict[StageElement, AbstractStageResultEntity | None] = OrderedDict()
        for element in stage_path:
            result = None
            if element.stage == Stage.BUILD:
                result = self._student_stage_result_repo.get_build_result(student_id)
            elif element.stage == Stage.COMPILE:
                result = self._student_stage_result_repo.get_compile_result(student_id)
            elif element.stage == Stage.EXECUTE:
                result = self._student_stage_result_repo.get_execute_result(student_id, element.testcase_id)
            elif element.stage == Stage.TEST:
                result = self._student_stage_result_repo.get_test_result(student_id, element.testcase_id)
            
            stage_results[element] = result
            
        return stage_results


class StudentStagePathResultEntityCheckTimestampQueryService(
    IStudentStagePathResultEntityCheckTimestampQueryService,
):
    def __init__(
            self,
            *,
            student_stage_result_repo: IStudentStageResultRepository,
    ):
        self._student_stage_result_repo = student_stage_result_repo

    def execute(self, student_id: StudentID) -> datetime | None:
        status = self._student_stage_result_repo.get_status(student_id)
        return status.timestamp
