from contextlib import contextmanager

from PyQt5.QtCore import QMutex

from domain.models.project_config import ProjectConfig
from files.core.project import ProjectCoreIO
from files.path_providers.project import ProjectPathProvider


class ProjectConfigRepository:
    def __init__(
            self,
            *,
            project_path_provider: ProjectPathProvider,
            project_core_io: ProjectCoreIO,
    ):
        self._project_path_provider = project_path_provider
        self._project_core_io = project_core_io

        self._lock = QMutex()
        self._project_config_cache: ProjectConfig | None = None

    @contextmanager
    def __lock(self):
        self._lock.lock()
        try:
            yield
        finally:
            self._lock.unlock()

    def __write_project_config_unlocked(self, project_config: ProjectConfig) -> None:
        json_fullpath = self._project_path_provider.config_json_fullpath()
        json_fullpath.parent.mkdir(parents=True, exist_ok=True)

        self._project_core_io.write_json(
            json_fullpath=json_fullpath,
            body=project_config.to_json(),
        )

        self._project_config_cache = project_config

    def __read_student_master_unlocked(self) -> ProjectConfig:
        if self._project_config_cache is not None:
            return self._project_config_cache

        json_fullpath = self._project_path_provider.config_json_fullpath()
        if not json_fullpath.exists():
            raise ValueError("ProjectConfig not created")

        body = self._project_core_io.read_json(
            json_fullpath=json_fullpath,
        )
        project_config = ProjectConfig.from_json(body)

        self._project_config_cache = project_config

        return project_config

    def put(self, project_config: ProjectConfig) -> None:
        with self.__lock():
            self.__write_project_config_unlocked(project_config)

    def get(self) -> ProjectConfig:
        with self.__lock():
            return self.__read_student_master_unlocked()

# TODO: ProjectIO の ProjectConfig関連を上のProjectConfigRepositoryに移植せよ！！
# TODO: ProjectIO の ProjectConfig関連を上のProjectConfigRepositoryに移植せよ！！
# TODO: ProjectIO の ProjectConfig関連を上のProjectConfigRepositoryに移植せよ！！
# TODO: ProjectIO の ProjectConfig関連を上のProjectConfigRepositoryに移植せよ！！
# TODO: ProjectIO の ProjectConfig関連を上のProjectConfigRepositoryに移植せよ！！
# TODO: ProjectIO の ProjectConfig関連を上のProjectConfigRepositoryに移植せよ！！
# TODO: ProjectIO の ProjectConfig関連を上のProjectConfigRepositoryに移植せよ！！
