from domain.models.values import TargetID, ProjectID
from services.project_create import ProjectCreateService


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
