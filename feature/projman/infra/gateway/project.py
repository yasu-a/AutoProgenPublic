from json import JSONDecodeError
from pathlib import Path
from typing import Callable

from feature.projman.domain.interface.gateway import IProjectListGateway, \
    IProjectConfigStateGateway, \
    ProjectConfigState, IProjectFileSystemGateway
from shared.domain.interface.gateway import IFolderShowInExplorerGateway
from shared.domain.interface.path_manager import IProjectPathManagerFactory
from shared.domain.interface.repository import IAppVersionProvider
from shared.domain.interface.system import IProjectCoreIOFactory
from shared.domain.value.app_version import AppVersion
from shared.domain.value.identifier import ProjectID


class ProjectListGateway(IProjectListGateway):
    def __init__(
            self,
            *,
            project_list_dir: Path,
    ):
        self._project_list_dir = project_list_dir

    def execute(self) -> list[ProjectID]:
        project_list_folder_fullpath = self._project_list_dir

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


class ProjectConfigStateGateway(IProjectConfigStateGateway):
    def __init__(
            self,
            *,
            project_path_manager_factory: IProjectPathManagerFactory,
            project_core_io_factory: IProjectCoreIOFactory,
            app_version_provider: IAppVersionProvider,
    ):
        self._project_path_manager_factory = project_path_manager_factory
        self._project_core_io_factory = project_core_io_factory
        self._app_version_provider = app_version_provider

    def analyze_state(self, project_id: ProjectID) -> ProjectConfigState:
        # JSONのパスを取得
        config_json_fullpath = self._project_path_manager_factory.create_path_manager(
            project_id=project_id,
        ).get_config_json_path()

        # JSONが存在するか確認
        if not config_json_fullpath.exists():
            # JSONが存在しないただのフォルダはUNOPENABLEとする
            return ProjectConfigState.UNOPENABLE

        # JSONを読み込む
        try:
            json_body = self._project_core_io_factory.create_project_core_io(
                project_id=project_id,
            ).read_json(
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
        current_app_version = self._app_version_provider.provide()
        if not AppVersion.is_compatible(
                current_version=current_app_version,
                target_version=config_app_version,
        ):  # 完全に一致す場合のみ互換性あり
            return ProjectConfigState.INCOMPATIBLE_APP_VERSION

        # JSONのすべての内容を読み出す
        try:
            from shared.domain.entity.project import ProjectEntity
            project_entity = ProjectEntity.from_json(json_body)
        except (KeyError, IndexError, ValueError):
            return ProjectConfigState.META_BROKEN
        if project_entity.project_id != project_id:
            return ProjectConfigState.META_BROKEN

        # プロジェクトが開けるかどうか確認
        if not project_entity.is_openable():
            return ProjectConfigState.UNOPENABLE

        return ProjectConfigState.NORMAL


class ProjectFileSystemGateway(IProjectFileSystemGateway):
    def __init__(
            self,
            *,
            project_folder_fullpath: Callable[[ProjectID], Path],
            project_list_folder_fullpath: Path,
            project_core_io_factory: IProjectCoreIOFactory,
            folder_show_in_explorer_gateway: IFolderShowInExplorerGateway,
    ):
        self._project_folder_fullpath = project_folder_fullpath
        self._project_list_folder_fullpath = project_list_folder_fullpath
        self._project_core_io_factory = project_core_io_factory
        self._folder_show_in_explorer_gateway = folder_show_in_explorer_gateway

    def get_size(self, project_id: ProjectID) -> int:
        project_folder_fullpath = self._project_folder_fullpath(project_id)
        size = self._project_core_io_factory.create_project_core_io(
            project_id=project_id,
        ).get_folder_size(
            folder_fullpath=project_folder_fullpath,
        )
        return size

    def show_base_folder(self) -> None:
        self._folder_show_in_explorer_gateway.execute(self._project_list_folder_fullpath)

    def show_folder(self, project_id: ProjectID) -> None:
        project_folder_fullpath = self._project_folder_fullpath(project_id)
        self._folder_show_in_explorer_gateway.execute(project_folder_fullpath)
