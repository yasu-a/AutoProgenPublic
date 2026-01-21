from abc import ABC, abstractmethod
from pathlib import Path

from shared.domain.value.identifier import ProjectID, StorageID, StudentID


class IAppPathManager(ABC):
    @abstractmethod
    def get_global_dir(self) -> Path:
        raise NotImplementedError()

    @abstractmethod
    def get_static_dir(self) -> Path:
        raise NotImplementedError()

    @abstractmethod
    def get_setting_json_path(self) -> Path:
        raise NotImplementedError()

    @abstractmethod
    def get_test_source_c_path(self) -> Path:
        raise NotImplementedError()

    @abstractmethod
    def get_app_version_json_path(self) -> Path:
        raise NotImplementedError()

    @abstractmethod
    def get_project_list_dir(self) -> Path:
        raise NotImplementedError()

    @abstractmethod
    def get_project_dir(self, project_id: ProjectID) -> Path:
        raise NotImplementedError()

    @abstractmethod
    def get_icon_path(self, filename: str) -> Path:
        raise NotImplementedError()

    @abstractmethod
    def get_image_path(self, filename: str) -> Path:
        raise NotImplementedError()

    @abstractmethod
    def get_vs_compiler_search_start_locations(self) -> list[Path]:
        raise NotImplementedError()


class IProjectPathManager(ABC):
    @abstractmethod
    def get_base_dir(self) -> Path:
        raise NotImplementedError()

    @abstractmethod
    def get_config_json_path(self) -> Path:
        raise NotImplementedError()

    @abstractmethod
    def get_testcase_base_dir(self) -> Path:
        raise NotImplementedError()

    @abstractmethod
    def get_database_path(self) -> Path:
        raise NotImplementedError()

    @abstractmethod
    def get_storage_dir(self, storage_id: StorageID) -> Path:
        raise NotImplementedError()

    @abstractmethod
    def get_student_submission_dir(self, student_id: StudentID) -> Path:
        raise NotImplementedError()


class IProjectPathManagerFactory(ABC):
    @abstractmethod
    def create_path_manager(self, project_id: ProjectID) -> IProjectPathManager:
        raise NotImplementedError()
