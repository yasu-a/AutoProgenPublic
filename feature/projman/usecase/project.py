from datetime import datetime

from feature.projman.usecase.dto import NormalProjectSummary, ErrorProjectSummary
from feature.projman.usecase.dto import ProjectConfigState
from feature.projman.usecase.interface import (
    IProjectCheckExistByNameUseCase,
    IProjectCreateUseCase,
    IProjectDeleteUseCase,
    IProjectGetSizeQueryUseCase,
    IProjectUpdateLastOpenedUseCase,
    IProjectListRecentSummaryUseCase,
    IProjectBaseFolderShowUseCase,
    IProjectFolderShowUseCase,
    IProjectListGateway,
    IProjectConfigStateGateway,
    IProjectFileSystemGateway,
)
from shared.domain.interface.repository import IAppVersionProvider
from shared.domain.entity.project import ProjectEntity
from shared.domain.value.identifier import ProjectID, TargetID
from shared.infra.repository.project import ProjectRepository


class ProjectCheckExistByNameUseCase(IProjectCheckExistByNameUseCase):
    # プロジェクト名に対応するプロジェクトが既に存在するかを確認する

    def __init__(
            self,
            *,
            project_list_gateway: IProjectListGateway,
    ):
        self._project_list_gateway = project_list_gateway

    def execute(self, target_project_name: str) -> bool:
        target_project_id = ProjectID(target_project_name)

        project_ids: list[ProjectID] = self._project_list_gateway.execute()
        for project_id in project_ids:
            if target_project_id == project_id:
                return True

        return False


class ProjectCreateUseCase(IProjectCreateUseCase):
    def __init__(
            self,
            *,
            project_repo: ProjectRepository,
            app_version_provider: IAppVersionProvider,
    ):
        self._project_repo = project_repo
        self._app_version_provider = app_version_provider

    def execute(self, project_name: str, target_number: int, zip_name: str) -> ProjectID:
        project_id = ProjectID(project_name)
        target_id = TargetID(target_number)
        project_entity = ProjectEntity(
            app_version=self._app_version_provider.provide(),
            project_id=project_id,
            target_id=target_id,
            created_at=datetime.now(),
            zip_name=zip_name,
            open_at=datetime.now(),
            is_initialized=False,
        )
        self._project_repo.put(project_entity)
        return project_id


class ProjectDeleteUseCase(IProjectDeleteUseCase):
    def __init__(
            self,
            *,
            project_repo: ProjectRepository,
    ):
        self._project_repo = project_repo

    def execute(self, project_id: ProjectID) -> None:
        self._project_repo.delete(project_id)


class ProjectGetSizeQueryUseCase(IProjectGetSizeQueryUseCase):
    def __init__(
            self,
            *,
            project_file_system_gateway: IProjectFileSystemGateway,
    ):
        self._project_file_system_gateway = project_file_system_gateway

    def execute(self, project_id: ProjectID) -> int:
        return self._project_file_system_gateway.get_size(project_id)


class ProjectUpdateLastOpenedUseCase(IProjectUpdateLastOpenedUseCase):
    """
    プロジェクトの最終開いた時刻を更新するUseCase
    ドメインロジックのみを担当（Stateの更新は含まない）
    """

    def __init__(
            self,
            *,
            project_repo: ProjectRepository,
    ):
        self._project_repo = project_repo

    def execute(self, project_id: ProjectID) -> None:
        """プロジェクトの最終開いた時刻を更新"""
        now = datetime.now()
        project_entity = self._project_repo.get(project_id)
        project_entity.open_at = now
        self._project_repo.put(project_entity)


class ProjectListRecentSummaryUseCase(IProjectListRecentSummaryUseCase):
    def __init__(
            self,
            *,
            project_list_gateway: IProjectListGateway,
            project_config_state_gateway: IProjectConfigStateGateway,
            project_repo: ProjectRepository,
    ):
        self._project_list_gateway = project_list_gateway
        self._project_config_state_gateway = project_config_state_gateway
        self._project_repo = project_repo

    def execute(self) -> list[NormalProjectSummary]:
        project_ids = self._project_list_gateway.execute()
        project_summaries = []
        for project_id in project_ids:
            project_config_state = self._project_config_state_gateway.execute(project_id)
            if project_config_state == ProjectConfigState.NORMAL:
                project_entity = self._project_repo.get(project_id)
                project_summary = NormalProjectSummary(
                    project_id=project_entity.project_id,
                    target_number=int(project_entity.target_id),
                    zip_name=project_entity.zip_name,
                    open_at=project_entity.open_at,
                )
            elif project_config_state == ProjectConfigState.INCOMPATIBLE_APP_VERSION:
                project_summary = ErrorProjectSummary(
                    project_id=project_id,
                    error_message="現在のバージョンと互換性がありません",
                )
            elif project_config_state == ProjectConfigState.UNOPENABLE:
                project_summary = ErrorProjectSummary(
                    project_id=project_id,
                    error_message="プロジェクトデータが破損していて開けません",
                )
            elif project_config_state == ProjectConfigState.META_BROKEN:
                project_summary = ErrorProjectSummary(
                    project_id=project_id,
                    error_message="メタデータが破損していて読み取れません",
                )
            else:
                assert False, project_config_state
            project_summaries.append(project_summary)

        project_summaries.sort()
        return project_summaries


class ProjectBaseFolderShowUseCase(IProjectBaseFolderShowUseCase):
    def __init__(
            self,
            *,
            project_file_system_gateway: IProjectFileSystemGateway,
    ):
        self._project_file_system_gateway = project_file_system_gateway

    def execute(self) -> None:
        self._project_file_system_gateway.show_base_folder()


class ProjectFolderShowUseCase(IProjectFolderShowUseCase):
    def __init__(
            self,
            *,
            project_file_system_gateway: IProjectFileSystemGateway,
    ):
        self._project_file_system_gateway = project_file_system_gateway

    def execute(self, project_id: ProjectID) -> None:
        self._project_file_system_gateway.show_folder(project_id)
