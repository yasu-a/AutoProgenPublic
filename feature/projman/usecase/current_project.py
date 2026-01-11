from typing import Callable

from feature.projman.usecase.interface import (
    ICurrentProjectSummaryGetUseCase,
    ICurrentProjectInitializeStaticUseCase,
    IStudentMasterCreateUseCase,
    IStudentSubmissionExtractUseCase, NormalProjectSummary,
)
from feature.projman.usecase.interface import ProjectInitializeResultDto
from shared.domain.entity.project import ProjectEntity
from shared.domain.error import StudentMasterServiceError, StudentSubmissionServiceError
from shared.domain.interface.gateway import IDatabaseInitializeGateway
from shared.infra.repository.current_project import CurrentProjectRepository


class CurrentProjectSummaryGetUseCase(ICurrentProjectSummaryGetUseCase):
    def __init__(
            self,
            *,
            current_project_repo: CurrentProjectRepository,
    ):
        self._current_project_repo = current_project_repo

    def execute(self) -> NormalProjectSummary:
        project: ProjectEntity = self._current_project_repo.get()
        return NormalProjectSummary(
            project_id=project.project_id,
            target_number=int(project.target_id),
            zip_name=project.zip_name,
            open_at=project.open_at,
        )


class CurrentProjectInitializeStaticUseCase(ICurrentProjectInitializeStaticUseCase):
    # プロジェクトの静的データを初期化するユースケース

    def __init__(
            self,
            *,
            db_init_gateway: IDatabaseInitializeGateway,
            student_master_create_usecase: IStudentMasterCreateUseCase,
            student_submission_extract_usecase: IStudentSubmissionExtractUseCase,
            current_project_repo: CurrentProjectRepository,
    ):
        self._db_init_gateway = db_init_gateway
        self._student_master_create_usecase = student_master_create_usecase
        self._student_submission_extract_usecase = student_submission_extract_usecase
        self._current_project_repo = current_project_repo

    def execute(self, progress_callback: Callable[[str], None]) -> ProjectInitializeResultDto:
        # データベーススキーマを初期化
        progress_callback("データベースを初期化しています")
        self._db_init_gateway.initialize()
        
        # 生徒マスタの作成
        try:
            self._student_master_create_usecase.execute(progress_callback)
        except StudentMasterServiceError as e:
            return ProjectInitializeResultDto.create_error(
                message=e.reason,
            )

        # 提出ファイルの展開
        try:
            self._student_submission_extract_usecase.execute(progress_callback)
        except StudentSubmissionServiceError as e:
            return ProjectInitializeResultDto.create_error(
                message=e.reason,
            )

        progress_callback("初期化を完了しています")
        current_project = self._current_project_repo.get()
        current_project = current_project.set_initialized()
        self._current_project_repo.put(current_project)
        return ProjectInitializeResultDto.create_success()
