from typing import Callable

from domain.errors import StudentMasterServiceError, StudentSubmissionServiceError
from services.current_project import CurrentProjectGetService, CurrentProjectSetInitializedService
from services.student_master_create import StudentMasterCreateService
from services.student_submission import StudentSubmissionExtractService
from usecases.dto.project import NormalProjectSummary, ProjectInitializeResult


class CurrentProjectSummaryGetUseCase:
    def __init__(
            self,
            *,
            current_project_get_service: CurrentProjectGetService,
    ):
        self._current_project_get_service = current_project_get_service

    def execute(self) -> NormalProjectSummary:
        project = self._current_project_get_service.execute()
        return NormalProjectSummary(
            project_id=project.project_id,
            target_number=int(project.target_id),
            zip_name=project.zip_name,
            open_at=project.open_at,
        )


class CurrentProjectInitializeStaticUseCase:
    # プロジェクトの静的データを初期化するユースケース

    def __init__(
            self,
            *,
            student_master_create_service: StudentMasterCreateService,
            student_submission_extract_service: StudentSubmissionExtractService,
            current_project_set_initialized_service: CurrentProjectSetInitializedService,
    ):
        self._student_master_create_service = student_master_create_service
        self._student_submission_extract_service = student_submission_extract_service
        self._current_project_set_initialized_service = current_project_set_initialized_service

    def execute(self, callback: Callable[[str], None]) -> ProjectInitializeResult:
        callback("生徒マスタを生成しています")
        try:
            self._student_master_create_service.execute()
        except StudentMasterServiceError as e:
            return ProjectInitializeResult.create_error(
                message=e.reason,
            )
        callback("生徒の提出ファイルを展開しています")
        try:
            self._student_submission_extract_service.execute()
        except StudentSubmissionServiceError as e:
            return ProjectInitializeResult.create_error(
                message=e.reason,
            )
        callback("初期化を完了しています")
        self._current_project_set_initialized_service.execute()
        return ProjectInitializeResult.create_success()
