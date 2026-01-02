from typing import Callable

from feature.projman.usecase.dto import NormalProjectSummary, ProjectInitializeResult
from feature.projman.usecase.interface import (
    ICurrentProjectSummaryGetUseCase,
    ICurrentProjectInitializeStaticUseCase,
    IStudentMasterCreateUseCase,
    IStudentSubmissionExtractUseCase,
)
from shared.domain.error import StudentMasterServiceError, StudentSubmissionServiceError
from shared.infra.repository.current_project import CurrentProjectRepository


class CurrentProjectSummaryGetUseCase(ICurrentProjectSummaryGetUseCase):
    def __init__(
            self,
            *,
            current_project_repo: CurrentProjectRepository,
    ):
        self._current_project_repo = current_project_repo

    def execute(self) -> NormalProjectSummary:
        ProjectEntity = self._current_project_repo.get()
        return NormalProjectSummary(
            project_id=ProjectEntity.project_id,
            target_number=int(ProjectEntity.target_id),
            zip_name=ProjectEntity.zip_name,
            open_at=ProjectEntity.open_at,
        )


class CurrentProjectInitializeStaticUseCase(ICurrentProjectInitializeStaticUseCase):
    # プロジェクトの静的データを初期化するユースケース

    def __init__(
            self,
            *,
            student_master_create_usecase: IStudentMasterCreateUseCase,
            student_submission_extract_usecase: IStudentSubmissionExtractUseCase,
            current_project_repo: CurrentProjectRepository,
    ):
        self._student_master_create_usecase = student_master_create_usecase
        self._student_submission_extract_usecase = student_submission_extract_usecase
        self._current_project_repo = current_project_repo

    def execute(self, callback: Callable[[str], None]) -> ProjectInitializeResult:
        callback("生徒マスタを生成しています")
        try:
            self._student_master_create_usecase.execute()
        except StudentMasterServiceError as e:
            return ProjectInitializeResult.create_error(
                message=e.reason,
            )
        callback("生徒の提出ファイルを展開しています")
        try:
            self._student_submission_extract_usecase.execute()
        except StudentSubmissionServiceError as e:
            return ProjectInitializeResult.create_error(
                message=e.reason,
            )
        callback("初期化を完了しています")
        current_project = self._current_project_repo.get()
        current_project = current_project.set_initialized()
        self._current_project_repo.put(current_project)
        return ProjectInitializeResult.create_success()
