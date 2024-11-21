from domain.models.project import Project
from infra.repositories.current_project import CurrentProjectRepository


class CurrentProjectGetService:
    def __init__(
            self,
            *,
            current_project_repo: CurrentProjectRepository,
    ):
        self._current_project_repo = current_project_repo

    def execute(self) -> Project:
        return self._current_project_repo.get()


class CurrentProjectSetInitializedService:
    def __init__(
            self,
            *,
            current_project_repo: CurrentProjectRepository,
    ):
        self._current_project_repo = current_project_repo

    def execute(self) -> None:
        current_project = self._current_project_repo.get()
        current_project = current_project.set_initialized()
        self._current_project_repo.put(current_project)
