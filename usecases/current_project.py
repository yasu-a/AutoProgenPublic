from services.current_project import CurrentProjectGetService
from usecases.dto.project_summary import ProjectSummary


class CurrentProjectSummaryGetUseCase:
    def __init__(
            self,
            *,
            current_project_get_service: CurrentProjectGetService,
    ):
        self._current_project_get_service = current_project_get_service

    def execute(self) -> ProjectSummary:
        project = self._current_project_get_service.execute()
        return ProjectSummary(
            project_id=project.project_id,
            project_name=str(project.project_id),
            target_number=int(project.target_id),
            zip_name=project.zip_name,
            open_at=project.open_at,
        )
