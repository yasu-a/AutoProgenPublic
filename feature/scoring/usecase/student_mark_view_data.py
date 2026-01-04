from feature.scoring.usecase.interface import IStudentMarkViewDataGetMarkSummaryUseCase, \
    AbstractStudentTestCaseTestResultViewData, \
    StudentTestCaseTestResultAcceptedViewData, StudentTestCaseTestResultWrongAnswerViewData, \
    StudentTestCaseTestResultUntestableViewData, IStudentMarkViewDataGetTestResultUseCase
from feature.scoring.usecase.interface import StudentMarkEntitySummaryViewDataDto, \
    StudentMarkEntityState
from shared.domain.interface.service import IStagePathListSubService, \
    IStudentMarkEntityGetSubService, IStudentGetStagePathResultMapService, \
    IStudentStagePathResultEntityCheckRollbackService, IStudentStagePathResultAnalyzerService
from shared.domain.model.stage import StageElement, Stage
from shared.domain.model.student_result import TestStageResultEntity
from shared.domain.service.stage_path import StagePathGetByTestCaseIDService
from shared.domain.value.identifier import StudentID, TestCaseID
from shared.infra.repository.student import StudentRepository


class StudentMarkViewDataGetTestResultUseCase(IStudentMarkViewDataGetTestResultUseCase):
    def __init__(
            self,
            *,
            stage_path_get_by_testcase_id_service: StagePathGetByTestCaseIDService,
            student_get_stage_path_result_map_service: IStudentGetStagePathResultMapService,
            student_stage_path_result_analyzer_service: IStudentStagePathResultAnalyzerService,
    ):
        self._stage_path_get_by_testcase_id_service \
            = stage_path_get_by_testcase_id_service
        self._student_get_stage_path_result_map_service \
            = student_get_stage_path_result_map_service
        self._student_stage_path_result_analyzer_service \
            = student_stage_path_result_analyzer_service

    def execute(
            self,
            student_id: StudentID,
            testcase_id: TestCaseID,
    ) -> AbstractStudentTestCaseTestResultViewData:
        # 対象のステージパスを見つける
        stage_path = self._stage_path_get_by_testcase_id_service.execute(
            testcase_id)

        # このステージパスの結果を取得
        results_map = self._student_get_stage_path_result_map_service.execute(student_id, stage_path)

        if self._student_stage_path_result_analyzer_service.is_all_finished(stage_path, results_map):
            # すべてのステージが成功しているとき
            test_stage_element = next((e for e in stage_path if e.stage == Stage.TEST), None)
            assert test_stage_element is not None
            test_stage_result = results_map.get(test_stage_element)
            
            assert isinstance(test_stage_result,
                              TestStageResultEntity), test_stage_result
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
            reason = self._student_stage_path_result_analyzer_service.get_last_failure_detailed_reason(stage_path, results_map)
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
            student_mark_get_sub_service: IStudentMarkEntityGetSubService,
            stage_path_list_sub_service: IStagePathListSubService,
            student_get_stage_path_result_map_service: IStudentGetStagePathResultMapService,
            student_stage_path_result_check_rollback_service: IStudentStagePathResultEntityCheckRollbackService,
    ):
        self._student_repo \
            = student_repo
        self._student_mark_get_sub_service \
            = student_mark_get_sub_service
        self._stage_path_list_sub_service \
            = stage_path_list_sub_service
        self._student_get_stage_path_result_map_service \
            = student_get_stage_path_result_map_service
        self._student_stage_path_result_check_rollback_service \
            = student_stage_path_result_check_rollback_service

    def execute(self, student_id: StudentID) -> StudentMarkEntitySummaryViewDataDto:
        stage_path_lst: list[list[StageElement]] = self._stage_path_list_sub_service.execute()

        state: StudentMarkEntityState = StudentMarkEntityState.NO_TEST_FOUND
        detailed_text = None
        for stage_path in stage_path_lst:
            test_stage = next((s for s in stage_path if s.stage == Stage.TEST), None)
            if test_stage is None:
                # ステージパスにTestStageがない（テストケースが定義されていない）
                continue

            # このステージパスの結果を取得
            results_map = self._student_get_stage_path_result_map_service.execute(student_id, stage_path)

            # ロールバックの必要があるか確認
            is_rollback_required = self._student_stage_path_result_check_rollback_service.execute(
                student_id=student_id,
                stage_path=stage_path,
                results_map=results_map,
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
