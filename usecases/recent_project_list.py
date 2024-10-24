from services.project_list import ProjectListService
from usecases.dto.project_summary import ProjectSummary


class RecentProjectListUseCase:
    def __init__(
            self,
            *,
            project_list_service: ProjectListService,
    ):
        self._project_list_service = project_list_service

    def execute(self) -> list[ProjectSummary]:
        projects = self._project_list_service.execute()
        return [
            ProjectSummary(
                project_id=project.project_id,
                project_name=str(project.project_id),
                target_number=int(project.target_id),
                open_at=project.open_at,
            )
            for project in projects
        ]
