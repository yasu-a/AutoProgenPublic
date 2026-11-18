from autoprogen.infra.repository.current_project import CurrentProjectRepository


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
