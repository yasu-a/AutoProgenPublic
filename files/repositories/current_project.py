from domain.errors import ProjectIOError
from domain.models.project import Project
from domain.models.values import ProjectID
from files.repositories.project import ProjectRepository


class CurrentProjectRepository:
    # TODO: cacheの実装
    def __init__(
            self,
            *,
            current_project_id: ProjectID,
            project_repository: ProjectRepository,
    ):
        self._current_project_id = current_project_id
        self._project_repo = project_repository

    def get(self) -> Project:
        return self._project_repo.get(self._current_project_id)

    def put(self, project: Project) -> None:
        if project.project_id != self._current_project_id:
            raise ProjectIOError("`project` must be the current project")
        self._project_repo.put(project)
