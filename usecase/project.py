from datetime import datetime

from application.state.current_project import set_current_project_id
from domain.model.value import ProjectID, TargetID
from service.dto.project import ProjectConfigState
from service.project import ProjectCreateService, ProjectBaseFolderShowService, \
    ProjectFolderShowService, ProjectDeleteService, ProjectGetSizeQueryService, \
    ProjectUpdateTimestampService, ProjectListIDQueryService, ProjectGetService, \
    ProjectGetConfigStateQueryService
from usecase.dto.project import NormalProjectSummary, ErrorProjectSummary


class ProjectCheckExistByNameUseCase:
    # プロジェクト名に対応するプロジェクトが既に存在するかを確認する

    def __init__(
            self,
            *,
            project_list_id_query_service: ProjectListIDQueryService,
    ):
        self._project_list_id_query_service = project_list_id_query_service

    def execute(self, target_project_name: str) -> bool:
        target_project_id = ProjectID(target_project_name)

        project_ids: list[ProjectID] = self._project_list_id_query_service.execute()
        for project_id in project_ids:
            if target_project_id == project_id:
                return True

        return False


class ProjectCreateUseCase:
    def __init__(
            self,
            *,
            project_create_service: ProjectCreateService,
    ):
        self._project_create_service = project_create_service

    def execute(self, project_name: str, target_number: int, zip_name: str) -> ProjectID:
        project_id = ProjectID(project_name)
        target_id = TargetID(target_number)
        self._project_create_service.execute(
            project_id=project_id,
            target_id=target_id,
            zip_name=zip_name,
        )
        return project_id


class ProjectDeleteUseCase:
    def __init__(
            self,
            *,
            project_delete_service: ProjectDeleteService,
    ):
        self._project_delete_service = project_delete_service

    def execute(self, project_id: ProjectID) -> None:
        self._project_delete_service.execute(project_id)


class ProjectGetSizeQueryUseCase:
    def __init__(
            self,
            *,
            project_get_size_query_service: ProjectGetSizeQueryService,
    ):
        self._project_get_size_query_service = project_get_size_query_service

    def execute(self, project_id: ProjectID) -> int:
        return self._project_get_size_query_service.execute(project_id)


class ProjectOpenUseCase:
    def __init__(
            self,
            *,
            project_update_timestamp_service: ProjectUpdateTimestampService,
    ):
        self._project_update_timestamp_service = project_update_timestamp_service

    def execute(self, project_id: ProjectID) -> None:
        set_current_project_id(project_id)
        now = datetime.now()
        self._project_update_timestamp_service.execute(
            project_id=project_id,
            timestamp=now,
        )


class ProjectListRecentSummaryUseCase:
    def __init__(
            self,
            *,
            project_list_id_query_service: ProjectListIDQueryService,
            project_get_config_state_query_service: ProjectGetConfigStateQueryService,
            project_get_service: ProjectGetService,
    ):
        self._project_list_id_query_service = project_list_id_query_service
        self._project_get_config_state_query_service = project_get_config_state_query_service
        self._project_get_service = project_get_service

    def execute(self) -> list[NormalProjectSummary]:
        project_ids = self._project_list_id_query_service.execute()
        project_summaries = []
        for project_id in project_ids:
            project_config_state = self._project_get_config_state_query_service.execute(project_id)
            if project_config_state == ProjectConfigState.NORMAL:
                project = self._project_get_service.execute(project_id)
                project_summary = NormalProjectSummary(
                    project_id=project.project_id,
                    target_number=int(project.target_id),
                    zip_name=project.zip_name,
                    open_at=project.open_at,
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


class ProjectBaseFolderShowUseCase:
    def __init__(
            self,
            *,
            project_base_folder_show_service: ProjectBaseFolderShowService,
    ):
        self._project_base_folder_show_service = project_base_folder_show_service

    def execute(self) -> None:
        self._project_base_folder_show_service.execute()


class ProjectFolderShowUseCase:
    def __init__(
            self,
            *,
            project_folder_show_service: ProjectFolderShowService,
    ):
        self._project_folder_show_service = project_folder_show_service

    def execute(self, project_id: ProjectID) -> None:
        self._project_folder_show_service.execute(project_id)
