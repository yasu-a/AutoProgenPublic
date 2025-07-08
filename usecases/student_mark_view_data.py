from domain.models.stage_path import StagePath
from domain.models.stages import TestStage
from domain.models.student_stage_path_result import StudentStagePathResult
from domain.models.student_stage_result import TestSuccessStudentStageResult
from domain.models.values import StudentID, TestCaseID
from services.stage_path import StagePathListSubService, StagePathGetByTestCaseIDService
from services.student import StudentGetService
from services.student_mark import StudentMarkGetSubService
from services.student_stage_path_result import StudentStagePathResultGetService, \
    StudentStagePathResultCheckRollbackService
from usecases.dto.student_mark_view_data import AbstractStudentTestCaseTestResultViewData, \
    StudentTestCaseTestResultAcceptedViewData, \
    StudentTestCaseTestResultWrongAnswerViewData, StudentTestCaseTestResultUntestableViewData, \
    StudentMarkSummaryViewData, StudentMarkState


class StudentMarkViewDataGetTestResultUseCase:
    def __init__(
            self,
            *,
            stage_path_get_by_testcase_id_service: StagePathGetByTestCaseIDService,
            student_stage_path_result_get_service: StudentStagePathResultGetService,
    ):
        self._stage_path_get_by_testcase_id_service \
            = stage_path_get_by_testcase_id_service
        self._student_stage_path_result_get_service \
            = student_stage_path_result_get_service

    def execute(
            self,
            student_id: StudentID,
            testcase_id: TestCaseID,
    ) -> AbstractStudentTestCaseTestResultViewData:
        # 対象のステージパスを見つける
        stage_path = self._stage_path_get_by_testcase_id_service.execute(testcase_id)

        # このステージパスの結果を取得
        stage_path_result: StudentStagePathResult \
            = self._student_stage_path_result_get_service.execute(student_id, stage_path)

        if stage_path_result.are_all_stages_done():
            # すべてのステージが成功しているとき
            test_stage_result = stage_path_result.get_result_by_stage_type(TestStage)
            assert isinstance(test_stage_result, TestSuccessStudentStageResult), test_stage_result
            if test_stage_result.test_result_output_files.is_accepted:
                return StudentTestCaseTestResultAcceptedViewData(
                    student_id=student_id,
                    testcase_id=testcase_id,
                    output_and_results=test_stage_result.test_result_output_files,
                )
            else:
                return StudentTestCaseTestResultWrongAnswerViewData(
                    student_id=student_id,
                    testcase_id=testcase_id,
                    output_and_results=test_stage_result.test_result_output_files,
                )
        else:
            # 失敗しているとき
            reason = stage_path_result.get_detailed_reason()
            if reason is None:
                reason = "処理が未完了です"
            return StudentTestCaseTestResultUntestableViewData(
                student_id=student_id,
                testcase_id=testcase_id,
                reason=reason,
            )


class StudentMarkViewDataGetMarkSummaryUseCase:
    def __init__(
            self,
            *,
            student_get_service: StudentGetService,
            student_mark_get_sub_service: StudentMarkGetSubService,
            stage_path_list_sub_service: StagePathListSubService,
            student_stage_path_result_get_service: StudentStagePathResultGetService,
            student_stage_path_result_check_rollback_service: StudentStagePathResultCheckRollbackService,
    ):
        self._student_get_service \
            = student_get_service
        self._student_mark_get_sub_service \
            = student_mark_get_sub_service
        self._stage_path_list_sub_service \
            = stage_path_list_sub_service
        self._student_stage_path_result_get_service \
            = student_stage_path_result_get_service
        self._student_stage_path_result_check_rollback_service \
            = student_stage_path_result_check_rollback_service

    def execute(self, student_id: StudentID) -> StudentMarkSummaryViewData:
        stage_path_lst: list[StagePath] = self._stage_path_list_sub_service.execute()

        state: StudentMarkState = StudentMarkState.NO_TEST_FOUND
        detailed_text = None
        for stage_path in stage_path_lst:
            test_stage = stage_path.get_stage_by_stage_type(TestStage)
            if test_stage is None:
                # ステージパスにTestStageがない（テストケースが定義されていない）
                continue

            # このステージパスの結果を取得
            stage_path_result: StudentStagePathResult \
                = self._student_stage_path_result_get_service.execute(student_id, stage_path)

            # ロールバックの必要があるか確認
            is_rollback_required = self._student_stage_path_result_check_rollback_service.execute(
                student_id=student_id,
                stage_path_result=stage_path_result,
            ) is not None
            if is_rollback_required:
                state = StudentMarkState.RERUN_REQUIRED
                break

            state = StudentMarkState.READY

        return StudentMarkSummaryViewData(
            student=self._student_get_service.execute(student_id),
            mark=self._student_mark_get_sub_service.execute(student_id),
            state=state,
            detailed_text=detailed_text,
        )
