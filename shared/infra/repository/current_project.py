from contextlib import contextmanager

from PyQt5.QtCore import QMutex

from shared.domain.entity.project import ProjectEntity
from shared.domain.error import ProjectIOError
from shared.domain.value.identifier import ProjectID
from shared.infra.repository.project import ProjectRepository


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
        self.__cache: ProjectEntity | None = None

    @contextmanager
    def _lock(self):
        self.__lock.lock()
        try:
            yield
        finally:
            self.__lock.unlock()

    def get(self) -> ProjectEntity:
        with self._lock():
            if self.__cache is None:
                self.__cache = self._project_repo.get(self._current_project_id)
            return self.__cache

    def put(self, ProjectEntity: ProjectEntity) -> None:
        if ProjectEntity.project_id != self._current_project_id:
            raise ProjectIOError("`ProjectEntity` must be the current ProjectEntity")
        with self._lock():
            self._project_repo.put(ProjectEntity)
            self.__cache = ProjectEntity
