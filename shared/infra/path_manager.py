from abc import abstractmethod
from pathlib import Path
import sys

from shared.domain.interface.path_manager import IAppPathManager, ICurrentProjectPathManager, IProjectPathManager, IProjectPathManagerFactory
from shared.domain.value.identifier import ProjectID, StorageID, StudentID


class AppPathManager(IAppPathManager):
    def get_global_dir(self) -> Path:
        return Path(sys.argv[0]).resolve().parent

    def get_static_dir(self) -> Path:
        return self.get_global_dir() / "static"

    def get_setting_json_path(self) -> Path:
        return self.get_global_dir() / "settings.json"

    def get_test_source_c_path(self) -> Path:
        return self.get_global_dir() / "vctest" / "test.c"

    def get_app_version_json_path(self) -> Path:
        return self.get_global_dir() / "app_version.json"

    def get_project_list_dir(self) -> Path:
        return Path("~/AutoProgenProjects").expanduser().resolve()

    def get_project_dir(self, project_id: ProjectID) -> Path:
        return self.get_project_list_dir() / str(project_id)

    def get_icon_path(self, filename: str) -> Path:
        return self.get_static_dir() / "icon" / f"{filename}.png"

    def get_image_path(self, filename: str) -> Path:
        return self.get_static_dir() / "img" / f"{filename}.jpg"

    def get_vs_compiler_search_start_locations(self) -> list[Path]:
        return [Path(r"C:\Program Files\Microsoft Visual Studio")]


class ProjectPathManager(IProjectPathManager):
    def __init__(self, project_base_dir: Path):
        self._base_dir = project_base_dir

    def get_base_dir(self) -> Path:
        return self._base_dir

    def get_config_json_path(self) -> Path:
        return self._base_dir / "config.json"

    def get_testcase_base_dir(self) -> Path:
        return self._base_dir / "testcases"

    def get_database_path(self) -> Path:
        return self._base_dir / "dynamic" / "database.sqlite3"

    def get_storage_dir(self, storage_id: StorageID) -> Path:
        return self._base_dir / "dynamic" / "StorageEntity" / str(storage_id)

    def get_student_submission_dir(self, student_id: StudentID) -> Path:
        return self._base_dir / "static" / "reports" / str(student_id)


class ProjectPathManagerFactory(IProjectPathManagerFactory):
    def __init__(self, app_path_manager: IAppPathManager):
        self._app_path_manager = app_path_manager

    def create_path_manager(self, project_id: ProjectID) -> IProjectPathManager:
        project_base_dir = self._app_path_manager.get_project_dir(project_id)
        return ProjectPathManager(project_base_dir=project_base_dir)
