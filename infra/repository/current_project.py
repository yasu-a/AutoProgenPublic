from contextlib import contextmanager

from PyQt5.QtCore import QMutex

from domain.error import ProjectIOError
from domain.model.project import Project
from domain.model.value import ProjectID
from infra.repository.project import ProjectRepository


class CurrentProjectRepository:
    # TODO: cacheの実装
    def __init__(
            self,
            *,
            current_project_id: ProjectID,
            project_repo: ProjectRepository,
    ):
        self._current_project_id = current_project_id
        self._project_repo = project_repo

        self.__lock = QMutex()
        self.__cache: Project | None = None

    @contextmanager
    def _lock(self):
        self.__lock.lock()
        try:
            yield
        finally:
            self.__lock.unlock()

    def get(self) -> Project:
        with self._lock():
            if self.__cache is None:
                self.__cache = self._project_repo.get(self._current_project_id)
            return self.__cache

    def put(self, project: Project) -> None:
        if project.project_id != self._current_project_id:
            raise ProjectIOError("`project` must be the current project")
        with self._lock():
            self._project_repo.put(project)
            self.__cache = project
