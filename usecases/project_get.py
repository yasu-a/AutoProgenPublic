from domain.models.project import Project
from domain.models.values import ProjectID
from services.project_list import ProjectListService


class ProjectNameExistUseCase:
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
