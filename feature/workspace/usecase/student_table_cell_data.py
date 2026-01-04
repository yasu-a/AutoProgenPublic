from feature.workspace.usecase.interface import (
    IStudentTableGetStudentIDCellDataUseCase,
    IStudentTableGetStudentNameCellDataUseCase,
    IStudentTableGetStudentStageStateCellDataUseCase,
    IStudentTableGetStudentErrorCellDataUseCase,
    StudentIDCellDataDto,
    StudentNameCellDataDto,
    StudentStageStateCellDataDto,
    StudentStageStateCellDataStageState,
    StudentErrorCellDataDto,
    StudentErrorCellDataTextEntryDto,
)
from shared.domain.service.stage_path import StagePathListSubService
from shared.domain.service.student_stage_path_result import StudentGetStagePathResultEntityService
from shared.domain.value.identifier import StudentID
from shared.domain.value.stage import AbstractStage
from shared.domain.value.stage_path import StagePath
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


class StudentTableGetStudentStageStateCellDataUseCase(IStudentTableGetStudentStageStateCellDataUseCase):
    # テーブル表示におけるHOTSPOT

    def __init__(
            self,
            *,
            stage_path_list_sub_service: StagePathListSubService,
            student_get_stage_path_result_entity_service: StudentGetStagePathResultEntityService,

    ):
        self._stage_path_list_sub_service = stage_path_list_sub_service
        self._student_get_stage_path_result_entity_service = student_get_stage_path_result_entity_service

    def execute(self, student_id: StudentID, stage_type: type[AbstractStage]) \
            -> StudentStageStateCellDataDto:
        stage_paths = self._stage_path_list_sub_service.execute()
        states: dict[StagePath, StudentStageStateCellDataStageState] = {}
        for stage_path in stage_paths:
            stage_path_result = self._student_get_stage_path_result_entity_service.execute(
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
        return StudentStageStateCellDataDto(
            student_id=student_id,
            stage_type=stage_type,
            states=states,
        )


class StudentTableGetStudentErrorCellDataUseCase(IStudentTableGetStudentErrorCellDataUseCase):
    def __init__(
            self,
            *,
            stage_path_list_sub_service: StagePathListSubService,
            student_get_stage_path_result_entity_service: StudentGetStagePathResultEntityService,
    ):
        self._stage_path_list_sub_service = stage_path_list_sub_service
        self._student_get_stage_path_result_entity_service = student_get_stage_path_result_entity_service

    def execute(self, student_id: StudentID) -> StudentErrorCellDataDto:
        stage_paths = self._stage_path_list_sub_service.execute()
        text_entries = []
        for stage_path in stage_paths:
            stage_path_result = self._student_get_stage_path_result_entity_service.execute(
                student_id=student_id,
                stage_path=stage_path,
            )
            summary_text = stage_path_result.last_stage_main_reason or ""
            detailed_text = stage_path_result.last_stage_detailed_reason or ""
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
