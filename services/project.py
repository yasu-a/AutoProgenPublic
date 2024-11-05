from datetime import datetime

from domain.models.project import Project
from domain.models.values import ProjectID, TargetID
from infra.core.project import ProjectCoreIO
from infra.external.project_base_folder_show_in_explorer import ProjectFolderShowInExplorerIO
from infra.path_providers.project import ProjectPathProvider
from infra.repositories.project import ProjectRepository
from utils.app_logging import create_logger


class ProjectListService:
    _logger = create_logger()

    def __init__(
            self,
            *,
            project_repo: ProjectRepository,
    ):
        self._project_repo = project_repo

    def execute(self) -> list[Project]:
        return self._project_repo.list()


class ProjectCreateService:
    # プロジェクトIDと設問IDとmanabaのzipアーカイブの名前から新規にプロジェクトを生成する

    def __init__(
            self,
            *,
            project_repo: ProjectRepository,
    ):
        self._project_repo = project_repo

    def execute(self, project_id: ProjectID, target_id: TargetID, zip_name: str) -> None:
        project = Project(
            project_id=project_id,
            target_id=target_id,
            created_at=datetime.now(),
            zip_name=zip_name,
            open_at=datetime.now(),
        )
        self._project_repo.put(project)


class ProjectUpdateTimestampService:
    def __init__(
            self,
            *,
            project_repo: ProjectRepository,
    ):
        self._project_repo = project_repo

    def execute(self, project_id: ProjectID, timestamp: datetime) -> None:
        project = self._project_repo.get(project_id)
        project.open_at = timestamp
        self._project_repo.put(project)


class ProjectDeleteService:
    def __init__(
            self,
            *,
            project_repo: ProjectRepository,
    ):
        self._project_repo = project_repo

    def execute(self, project_id: ProjectID) -> None:
        self._project_repo.delete(project_id)


class ProjectGetSizeQueryService:
    def __init__(
            self,
            *,
            project_path_provider: ProjectPathProvider,
            project_core_io: ProjectCoreIO,
    ):
        self._project_path_provider = project_path_provider
        self._project_core_io = project_core_io

    def execute(self, project_id: ProjectID) -> int:
        project_folder_fullpath = self._project_path_provider.base_folder_fullpath(project_id)
        size = self._project_core_io.get_folder_size(
            project_id=project_id,
            folder_fullpath=project_folder_fullpath,
        )
        return size


class ProjectBaseFolderShowService:
    def __init__(
            self,
            *,
            project_folder_show_in_explorer_io: ProjectFolderShowInExplorerIO,
    ):
        self._project_folder_show_in_explorer_io = project_folder_show_in_explorer_io

    def execute(self) -> None:
        self._project_folder_show_in_explorer_io.show_base_folder()


class ProjectFolderShowService:
    def __init__(
            self,
            *,
            project_folder_show_in_explorer_io: ProjectFolderShowInExplorerIO,
    ):
        self._project_folder_show_in_explorer_io = project_folder_show_in_explorer_io

    def execute(self, project_id: ProjectID) -> None:
        self._project_folder_show_in_explorer_io.show_folder(project_id)
