from feature.workspace.usecase.interface import (
    IStudentTableGetStudentIDCellDataUseCase,
    IStudentTableGetStudentNameCellDataUseCase,
    IStudentTableGetStudentStageStateCellDataUseCase,
    IStudentTableGetStudentErrorCellDataUseCase,
    StudentIDCellDataDto,
    StudentNameCellDataDto,
    StudentStageStateCellDataDto,
    StudentErrorCellDataDto,
    StudentErrorCellDataTextEntryDto,
)
from shared.domain.interface.service import IStagePathListSubService, \
    IStudentGetStagePathResultMapService, IStudentStagePathResultAnalyzerService
from shared.domain.model.stage import StageElement, Stage
from shared.domain.model.student_result import StudentStageStatusFlag
from shared.domain.value.identifier import StudentID
from shared.infra.repository.student import StudentRepository


class StudentTableGetStudentIDCellDataUseCase(IStudentTableGetStudentIDCellDataUseCase):
    def __init__(
            self,
            *,
            student_repo: StudentRepository,
    ):
        self._student_repo = student_repo

    def execute(self, student_id: StudentID) -> StudentIDCellDataDto:
        does_submission_exist = self._student_repo.get(student_id).is_submitted
        return StudentIDCellDataDto(
            student_id=student_id,
            is_submission_folder_link_alive=does_submission_exist,
        )


class StudentTableGetStudentNameCellDataUseCase(IStudentTableGetStudentNameCellDataUseCase):
    def __init__(
            self,
            *,
            student_repo: StudentRepository,
    ):
        self._student_repo = student_repo

    def execute(self, student_id: StudentID) -> StudentNameCellDataDto:
        student_entity = self._student_repo.get(student_id)
        return StudentNameCellDataDto(
            student_id=student_id,
            student_name=student_entity.name,
        )


class StudentTableGetStudentStageStateCellDataUseCase(
    IStudentTableGetStudentStageStateCellDataUseCase):

    def __init__(
            self,
            *,
            stage_path_list_sub_service: IStagePathListSubService,
            student_get_stage_path_result_map_service: IStudentGetStagePathResultMapService,

    ):
        self._stage_path_list_sub_service = stage_path_list_sub_service
        self._student_get_stage_path_result_map_service = student_get_stage_path_result_map_service

    def execute(self, student_id: StudentID, stage_type: Stage) \
            -> StudentStageStateCellDataDto:
        stage_paths = self._stage_path_list_sub_service.execute()
        states: dict[tuple[StageElement, ...], StudentStageStatusFlag] = {}
        for stage_path in stage_paths:
            results_map = self._student_get_stage_path_result_map_service.execute(
                student_id=student_id,
                stage_path=stage_path,
            )
            
            stage_element = next((e for e in stage_path if e.stage == stage_type), None)
            
            stage_result = None
            if stage_element:
                stage_result = results_map.get(stage_element)

            if stage_result is None:
                state = StudentStageStatusFlag.UNFINISHED
            elif stage_result.is_success:
                state = StudentStageStatusFlag.FINISHED_SUCCESS
            else:
                state = StudentStageStatusFlag.FINISHED_FAILURE
            states[tuple(stage_path)] = state
        return StudentStageStateCellDataDto(
            student_id=student_id,
            stage_type=stage_type,
            states=states,
        )


class StudentTableGetStudentErrorCellDataUseCase(IStudentTableGetStudentErrorCellDataUseCase):
    def __init__(
            self,
            *,
            stage_path_list_sub_service: IStagePathListSubService,
            student_get_stage_path_result_map_service: IStudentGetStagePathResultMapService,
            student_stage_path_result_analyzer_service: IStudentStagePathResultAnalyzerService,
    ):
        self._stage_path_list_sub_service = stage_path_list_sub_service
        self._student_get_stage_path_result_map_service = student_get_stage_path_result_map_service
        self._student_stage_path_result_analyzer_service = student_stage_path_result_analyzer_service

    def execute(self, student_id: StudentID) -> StudentErrorCellDataDto:
        stage_paths = self._stage_path_list_sub_service.execute()
        text_entries = []
        for stage_path in stage_paths:
            results_map = self._student_get_stage_path_result_map_service.execute(
                student_id=student_id,
                stage_path=stage_path,
            )
            summary_text = self._student_stage_path_result_analyzer_service.get_last_failure_main_reason(stage_path, results_map) or ""
            detailed_text = self._student_stage_path_result_analyzer_service.get_last_failure_detailed_reason(stage_path, results_map) or ""
            if summary_text or detailed_text:
                text_entries.append(
                    StudentErrorCellDataTextEntryDto(
                        summary_text=summary_text,
                        detailed_text=detailed_text,
                    )
                )
        return StudentErrorCellDataDto(
            student_id=student_id,
            text_entries=text_entries,
        )
