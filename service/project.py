from datetime import datetime
from json import JSONDecodeError

from domain.model.app_version import AppVersion
from domain.model.project import Project
from domain.model.value import ProjectID
from infra.io.files.project import ProjectCoreIO
from infra.repository.app_version import AppVersionRepository
from infra.repository.project_2 import ProjectRepository
from service.dto.project import ProjectConfigState


class ProjectGetConfigStateQueryService:
    def __init__(
            self,
            *,
            project_repo: ProjectRepository,
            project_core_io: ProjectCoreIO,
            app_version_repo: AppVersionRepository,
    ):
        self._project_repo = project_repo
        self._project_core_io = project_core_io
        self._app_version_repo = app_version_repo

    def execute(self, project_id: ProjectID) -> ProjectConfigState:
        # JSONのパスを取得
        layout = self._project_repo.create_project_path_layout(project_id)
        config_json_fullpath = layout.config_json

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
        current_app_version = self._app_version_repo.get()
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


class ProjectListIDQueryService:  # TODO: 薄いので廃止したい
    def __init__(
            self,
            *,
            project_repo: ProjectRepository,
    ):
        self._project_repo = project_repo

    def execute(self) -> list[ProjectID]:
        return self._project_repo.list_ids()


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


class ProjectGetSizeQueryService:
    def __init__(
            self,
            *,
            project_repo: ProjectRepository,
            project_core_io: ProjectCoreIO,
    ):
        self._project_repo = project_repo
        self._project_core_io = project_core_io

    def execute(self, project_id: ProjectID) -> int:
        layout = self._project_repo.create_project_path_layout(project_id)
        project_folder_fullpath = layout.root
        size = self._project_core_io.get_folder_size(
            project_id=project_id,
            folder_fullpath=project_folder_fullpath,
        )
        return size
