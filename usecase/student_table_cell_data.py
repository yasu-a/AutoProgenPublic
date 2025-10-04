from domain.model.stage_path import StagePath
from domain.model.stage import AbstractStage
from domain.model.value import StudentID
from service.stage_path import StagePathListSubService
from service.student import StudentGetService
from service.student_stage_path_result import StudentStagePathResultGetService
from service.student_submission import StudentSubmissionExistService
from usecase.dto.student_table_cell_data import StudentIDCellData, StudentNameCellData, \
    StudentStageStateCellData, StudentStageStateCellDataStageState, StudentErrorCellData, \
    StudentErrorCellDataTextEntry


class StudentTableGetStudentIDCellDataUseCase:
    def __init__(
            self,
            *,
            student_submission_exist_service: StudentSubmissionExistService,
    ):
        self._student_submission_exist_service = student_submission_exist_service

    def execute(self, student_id: StudentID) -> StudentIDCellData:
        student_number = str(student_id)
        does_submission_exist = self._student_submission_exist_service.execute(student_id)
        return StudentIDCellData(
            student_id=student_id,
            student_number=student_number,
            is_submission_folder_link_alive=does_submission_exist,
        )


class StudentTableGetStudentNameCellDataUseCase:
    def __init__(
            self,
            *,
            student_get_service: StudentGetService,
    ):
        self._student_get_service = student_get_service

    def execute(self, student_id: StudentID) -> StudentNameCellData:
        student = self._student_get_service.execute(student_id)
        return StudentNameCellData(
            student_id=student_id,
            student_name=student.name,
        )


class StudentTableGetStudentStageStateCellDataUseCase:
    # テーブル表示におけるHOTSPOT

    def __init__(
            self,
            *,
            stage_path_list_sub_service: StagePathListSubService,
            student_stage_path_result_get_service: StudentStagePathResultGetService,

    ):
        self._stage_path_list_sub_service = stage_path_list_sub_service
        self._student_stage_path_result_get_service = student_stage_path_result_get_service

    def execute(self, student_id: StudentID, stage_type: type[AbstractStage]) \
            -> StudentStageStateCellData:
        stage_paths = self._stage_path_list_sub_service.execute()
        states: dict[StagePath, StudentStageStateCellDataStageState] = {}
        for stage_path in stage_paths:
            stage_path_result = self._student_stage_path_result_get_service.execute(
                student_id=student_id,
                stage_path=stage_path,
            )
            stage_result = stage_path_result.get_result_by_stage_type(stage_type)
            if stage_result is None:
                state = StudentStageStateCellDataStageState.UNFINISHED
            elif stage_result.is_success:
                state = StudentStageStateCellDataStageState.FINISHED_SUCCESS
            else:
                state = StudentStageStateCellDataStageState.FINISHED_FAILURE
            states[stage_path] = state
        return StudentStageStateCellData(
            student_id=student_id,
            stage_type=stage_type,
            states=states,
        )


class StudentTableGetStudentErrorCellDataUseCase:
    def __init__(
            self,
            *,
            stage_path_list_sub_service: StagePathListSubService,
            student_stage_path_result_get_service: StudentStagePathResultGetService,
    ):
        self._stage_path_list_sub_service = stage_path_list_sub_service
        self._student_stage_path_result_get_service = student_stage_path_result_get_service

    def execute(self, student_id: StudentID) -> StudentErrorCellData:
        stage_paths = self._stage_path_list_sub_service.execute()
        text_entries = []
        for stage_path in stage_paths:
            stage_path_result = self._student_stage_path_result_get_service.execute(
                student_id=student_id,
                stage_path=stage_path,
            )
            summary_text = stage_path_result.last_stage_main_reason or ""
            detailed_text = stage_path_result.last_stage_detailed_reason or ""
            if summary_text or detailed_text:
                text_entries.append(
                    StudentErrorCellDataTextEntry(
                        summary_text=summary_text,
                        detailed_text=detailed_text,
                    )
                )
        return StudentErrorCellData(
            student_id=student_id,
            text_entries=text_entries,
        )
