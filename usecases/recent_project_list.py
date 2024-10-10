from services.project_list import ProjectListService
from usecases.dto.recent_project_summary import RecentProjectSummary


class RecentProjectListUseCase:
    def __init__(
            self,
            *,
            project_list_service: ProjectListService,
    ):
        self._project_list_service = project_list_service

    def execute(self) -> list[RecentProjectSummary]:
        projects = self._project_list_service.execute()
        return [
            RecentProjectSummary(
                project_id=project.project_id,
                project_name=str(project.project_id),
                target_number=int(project.target_id),
                mtime=project.open_at,
            )
            for project in projects
        ]
