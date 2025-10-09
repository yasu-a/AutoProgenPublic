from datetime import datetime
from json import JSONDecodeError

from domain.model.app_version import AppVersion
from domain.model.project import Project
from domain.model.value import ProjectID, TargetID
from infra.io.files.project import ProjectCoreIO
from infra.io.project_base_folder_show_in_explorer import ProjectFolderShowInExplorerIO
from infra.path_provider.project import ProjectPathProvider, ProjectListPathProvider
from infra.repository.project import ProjectRepository
from service.app_version import AppVersionGetService
from service.dto.project import ProjectConfigState


class ProjectGetConfigStateQueryService:
    def __init__(
            self,
            *,
            project_path_provider: ProjectPathProvider,
            project_core_io: ProjectCoreIO,
            app_version_get_service: AppVersionGetService,
    ):
        self._project_path_provider = project_path_provider
        self._project_core_io = project_core_io
        self._app_version_get_service = app_version_get_service

    def execute(self, project_id: ProjectID) -> ProjectConfigState:
        # JSONのパスを取得
        config_json_fullpath = self._project_path_provider.config_json_fullpath(project_id)

        # JSONが存在するか確認
        if not config_json_fullpath.exists():
            # JSONが存在しないただのフォルダはUNOPENABLEとする
            # raise ProjectServiceError(f"Project \"{project_id}\" not found")
            return ProjectConfigState.UNOPENABLE

        # JSONを読み込む
        try:
            json_body = self._project_core_io.read_json(
                project_id=project_id,
                json_fullpath=config_json_fullpath,
            )
        except (OSError, JSONDecodeError):
            return ProjectConfigState.META_BROKEN

        # バージョンだけ読み込む
        if "app_version" not in json_body:
            return ProjectConfigState.META_BROKEN
        try:
            config_app_version: AppVersion = AppVersion.from_json(json_body["app_version"])
        except (KeyError, IndexError, ValueError):
            return ProjectConfigState.META_BROKEN

        # バージョンに互換性があるかどうか確認
        current_app_version = self._app_version_get_service.execute()
        if not AppVersion.is_compatible(
                current_version=current_app_version,
                target_version=config_app_version,
        ):  # 完全に一致す場合のみ互換性あり
            return ProjectConfigState.INCOMPATIBLE_APP_VERSION

        # JSONのすべての内容を読み出す
        try:
            project = Project.from_json(json_body)
        except (KeyError, IndexError, ValueError):
            return ProjectConfigState.META_BROKEN
        if project.project_id != project_id:
            return ProjectConfigState.META_BROKEN

        # プロジェクトが開けるかどうか確認
        if not project.is_openable():
            return ProjectConfigState.UNOPENABLE

        return ProjectConfigState.NORMAL


class ProjectListIDQueryService:
    def __init__(
            self,
            *,
            project_list_path_provider: ProjectListPathProvider,
    ):
        self._project_list_path_provider = project_list_path_provider

    def execute(self) -> list[ProjectID]:
        project_list_folder_fullpath = self._project_list_path_provider.base_folder_fullpath()

        project_list_folder_fullpath.mkdir(parents=True, exist_ok=True)

        project_ids: list[ProjectID] = []
        for sub_folder_fullpath in project_list_folder_fullpath.iterdir():
            if not sub_folder_fullpath.is_dir():
                continue
            folder_name = sub_folder_fullpath.name
            try:
                maybe_project_id = ProjectID(folder_name)
            except ValueError:  # malformed folder name
                continue
            project_ids.append(maybe_project_id)

        return project_ids


class ProjectGetService:
    def __init__(
            self,
            *,
            project_repo: ProjectRepository,
    ):
        self._project_repo = project_repo

    def execute(self, project_id: ProjectID) -> Project:
        return self._project_repo.get(project_id)


class ProjectCreateService:
    # プロジェクトIDと設問IDとmanabaのzipアーカイブの名前から新規にプロジェクトを生成する

    def __init__(
            self,
            *,
            project_repo: ProjectRepository,
            app_version_get_service: AppVersionGetService,
    ):
        self._project_repo = project_repo
        self._app_version_get_service = app_version_get_service

    def execute(self, project_id: ProjectID, target_id: TargetID, zip_name: str) -> None:
        project = Project(
            app_version=self._app_version_get_service.execute(),
            project_id=project_id,
            target_id=target_id,
            created_at=datetime.now(),
            zip_name=zip_name,
            open_at=datetime.now(),
            is_initialized=False,
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
