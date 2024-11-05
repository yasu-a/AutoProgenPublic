from typing import Callable

from domain.models.project import Project
from domain.models.values import ProjectID, TargetID
from services.project import ProjectListService, ProjectCreateService
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

    def execute(self, project_name: str, target_number: int) -> ProjectID:
        project_id = ProjectID(project_name)
        target_id = TargetID(target_number)
        self._project_create_service.execute(
            project_id=project_id,
            target_id=target_id,
        )
        return project_id


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
                open_at=project.open_at,
            )
            for project in projects
        ]
        lst.sort(reverse=True)
        return lst
