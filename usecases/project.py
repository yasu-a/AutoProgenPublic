from datetime import datetime
from typing import Callable

from application.state.current_project import set_current_project_id
from domain.models.project import Project
from domain.models.values import ProjectID, TargetID
from services.project import ProjectListService, ProjectCreateService, ProjectBaseFolderShowService, \
    ProjectFolderShowService, ProjectDeleteService, ProjectGetSizeQueryService, \
    ProjectUpdateTimestampService
from services.student_master_create import StudentMasterCreateService
from services.student_submission import StudentSubmissionExtractService
from usecases.dto.project_summary import ProjectSummary


class ProjectCheckExistByNameUseCase:
    # プロジェクト名に対応するプロジェクトが既に存在するかを確認する

    def __init__(
            self,
            *,
            project_list_service: ProjectListService,
    ):
        self._project_list_service = project_list_service

    def execute(self, target_project_name: str) -> bool:
        target_project_id = ProjectID(target_project_name)

        projects: list[Project] = self._project_list_service.execute()
        for project in projects:
            if target_project_id == project.project_id:
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


class ProjectInitializeStaticUseCase:
    # プロジェクトの静的データを初期化するユースケース

    def __init__(
            self,
            *,
            student_master_create_service: StudentMasterCreateService,
            student_submission_extract_service: StudentSubmissionExtractService,
    ):
        self._student_master_create_service = student_master_create_service
        self._student_submission_extract_service = student_submission_extract_service

    def execute(self, callback: Callable[[str], None]) -> None:
        callback("生徒マスタを生成しています")
        self._student_master_create_service.execute()
        callback("生徒の提出ファイルを展開しています")
        self._student_submission_extract_service.execute()


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
            project_list_service: ProjectListService,
    ):
        self._project_list_service = project_list_service

    def execute(self) -> list[ProjectSummary]:
        projects = self._project_list_service.execute()
        lst = [
            ProjectSummary(
                project_id=project.project_id,
                project_name=str(project.project_id),
                target_number=int(project.target_id),
                zip_name=project.zip_name,
                open_at=project.open_at,
            )
            for project in projects
        ]
        lst.sort(reverse=True)
        return lst


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
