from domain.models.project import Project
from files.repositories.current_project import CurrentProjectRepository


class CurrentProjectGetService:
    def __init__(
            self,
            *,
            current_project_repo: CurrentProjectRepository,
    ):
        self._current_project_repo = current_project_repo

    def execute(self) -> Project:
        return self._current_project_repo.get()
