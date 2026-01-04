from feature.scoring.usecase.interface import IStudentMarkViewDataGetTestResultUseCase, \
    IStudentMarkViewDataGetMarkSummaryUseCase, AbstractStudentTestCaseTestResultViewData, \
    StudentTestCaseTestResultAcceptedViewData, StudentTestCaseTestResultWrongAnswerViewData, \
    StudentTestCaseTestResultUntestableViewData
from feature.scoring.usecase.interface import StudentMarkEntitySummaryViewDataDto, \
    StudentMarkEntityState
from shared.domain.entity.student_stage_path_result import StudentStagePathResultEntity
from shared.domain.service.stage_path import StagePathListSubService, \
    StagePathGetByTestCaseIDService
from shared.domain.service.student_mark_get import StudentMarkEntityGetSubService
from shared.domain.service.student_stage_path_result import StudentGetStagePathResultEntityService, \
    StudentStagePathResultEntityCheckRollbackService
from shared.domain.value.identifier import StudentID, TestCaseID
from shared.domain.value.stage import TestStage
from shared.domain.value.stage_path import StagePath
from shared.domain.value.student_stage_result import TestSuccessStudentStageResult
from shared.infra.repository.student import StudentRepository


class StudentMarkViewDataGetTestResultUseCase(IStudentMarkViewDataGetTestResultUseCase):
    def __init__(
            self,
            *,
            stage_path_get_by_testcase_id_service: StagePathGetByTestCaseIDService,
            student_get_stage_path_result_entity_service: StudentGetStagePathResultEntityService,
    ):
        self._stage_path_get_by_testcase_id_service \
            = stage_path_get_by_testcase_id_service
        self._student_get_stage_path_result_entity_service \
            = student_get_stage_path_result_entity_service

    def execute(
            self,
            student_id: StudentID,
            testcase_id: TestCaseID,
    ) -> AbstractStudentTestCaseTestResultViewData:
        # 対象のステージパスを見つける
        stage_path = self._stage_path_get_by_testcase_id_service.execute(
            testcase_id)

        # このステージパスの結果を取得
        stage_path_result: StudentStagePathResultEntity \
            = self._student_get_stage_path_result_entity_service.execute(student_id, stage_path)

        if stage_path_result.are_all_finished:
            # すべてのステージが成功しているとき
            test_stage_result = stage_path_result.get_result_by_stage_type(
                TestStage)
            assert isinstance(test_stage_result,
                              TestSuccessStudentStageResult), test_stage_result
            if test_stage_result.is_accepted:
                return StudentTestCaseTestResultAcceptedViewData(
                    student_id=student_id,
                    testcase_id=testcase_id,
                    output_and_results=test_stage_result.test_result_output_file_collection,
                )
            else:
                return StudentTestCaseTestResultWrongAnswerViewData(
                    student_id=student_id,
                    testcase_id=testcase_id,
                    output_and_results=test_stage_result.test_result_output_file_collection,
                )
        else:
            # 失敗しているとき
            reason = stage_path_result.last_stage_detailed_reason
            if reason is None:
                reason = "処理が未完了です"
            return StudentTestCaseTestResultUntestableViewData(
                student_id=student_id,
                testcase_id=testcase_id,
                reason=reason,
            )


class StudentMarkViewDataGetMarkSummaryUseCase(IStudentMarkViewDataGetMarkSummaryUseCase):
    def __init__(
            self,
            *,
            student_repo: StudentRepository,
            student_mark_get_sub_service: StudentMarkEntityGetSubService,
            stage_path_list_sub_service: StagePathListSubService,
            student_get_stage_path_result_entity_service: StudentGetStagePathResultEntityService,
            student_stage_path_result_check_rollback_service: StudentStagePathResultEntityCheckRollbackService,
    ):
        self._student_repo \
            = student_repo
        self._student_mark_get_sub_service \
            = student_mark_get_sub_service
        self._stage_path_list_sub_service \
            = stage_path_list_sub_service
        self._student_get_stage_path_result_entity_service \
            = student_get_stage_path_result_entity_service
        self._student_stage_path_result_check_rollback_service \
            = student_stage_path_result_check_rollback_service

    def execute(self, student_id: StudentID) -> StudentMarkEntitySummaryViewDataDto:
        stage_path_lst: list[StagePath] = self._stage_path_list_sub_service.execute(
        )

        state: StudentMarkEntityState = StudentMarkEntityState.NO_TEST_FOUND
        detailed_text = None
        for stage_path in stage_path_lst:
            test_stage = stage_path.get_stage_by_stage_type(TestStage)
            if test_stage is None:
                # ステージパスにTestStageがない（テストケースが定義されていない）
                continue

            # このステージパスの結果を取得
            stage_path_result: StudentStagePathResultEntity \
                = self._student_get_stage_path_result_entity_service.execute(student_id, stage_path)

            # ロールバックの必要があるか確認
            is_rollback_required = self._student_stage_path_result_check_rollback_service.execute(
                student_id=student_id,
                stage_path_result=stage_path_result,
            ) is not None
            if is_rollback_required:
                state = StudentMarkEntityState.RERUN_REQUIRED
                break

            state = StudentMarkEntityState.READY

        return StudentMarkEntitySummaryViewDataDto(
            student=self._student_repo.get(student_id),
            mark=self._student_mark_get_sub_service.execute(student_id),
            state=state,
            detailed_text=detailed_text,
        )
