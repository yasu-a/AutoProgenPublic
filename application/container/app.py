from application.container.project import ProjectContainer
from domain.model.value import ProjectID


class AppContainer:
    def create_project_container(self, project_id: ProjectID) -> "ProjectContainer":
        return ProjectContainer(
            app_container=self,
            project_id=project_id,
        )
