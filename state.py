import codecs
import json
import os

from PyQt5.QtCore import QObject, QMutex

from app_logging import create_logger
from bg_tasks import BackgroundTasks, BackgroundTaskDispatcher
from models.project import ProjectData
from services.project import ProjectService


class ProjectDataManager(QObject):
    _logger = create_logger()

    def __load_data(self):
        if os.path.exists(self.__project_data_path):
            with codecs.open(self.__project_data_path, "r", "utf-8") as f:
                return ProjectData.from_json(json.load(f))
        else:
            return ProjectData.create_empty()

    def __init__(self, project_data_path, parent: QObject = None):
        super().__init__(parent)

        self.__project_data_path = project_data_path
        self.__lock = QMutex()
        self.__modify_count = 0
        self.__modify_count_on_last_save = 0

        self.__data = self.__load_data()

    @property
    def modify_count(self):
        return self.__modify_count

    # @contextmanager
    def data(self, *, readonly=False):
        self_lock = self.__lock
        self_data = self.__data

        if readonly:
            class ProjectDataContextManager:
                def __enter__(self) -> ProjectData:
                    return self_data

                def __exit__(self, exc_type, exc_val, exc_tb):
                    return False
        else:
            class ProjectDataContextManager:
                def __enter__(self) -> ProjectData:
                    self_lock.lock()
                    return self_data

                def __exit__(self, exc_type, exc_val, exc_tb):
                    self_lock.unlock()
                    return False

        return ProjectDataContextManager()

    def commit(self):
        self.__modify_count += 1

    def _save(self):
        with self.data():
            os.makedirs(os.path.dirname(self.__project_data_path), exist_ok=True)
            with codecs.open(self.__project_data_path, "w", "utf-8") as f:
                json.dump(self.__data.to_json(), f, indent=2, ensure_ascii=False)
            self._logger.info("project data saved")
            self.__modify_count_on_last_save = self.__modify_count

    def is_changed_after_last_save(self):
        return self.__modify_count != self.__modify_count_on_last_save

    def save_if_necessary(self):
        if self.is_changed_after_last_save():
            self._save()


data_manager: ProjectDataManager | None = None
project_service: ProjectService | None = None
tasks: BackgroundTasks | None = None
task_dispatcher: BackgroundTaskDispatcher | None = None

_WORKING_DIR_RELATIVE_PATH = "__autoprogen__"


def data(readonly=False):
    return data_manager.data(readonly=readonly)


def commit_data():
    data_manager.commit()


def get_datafile_path(project_path):
    data_file_path = os.path.join(project_path, _WORKING_DIR_RELATIVE_PATH, "data.json")
    return data_file_path


def get_env_dir_path(project_path):
    env_dir_path = os.path.join(project_path, _WORKING_DIR_RELATIVE_PATH, "env")
    return env_dir_path


def create_project_service(project_path):
    return ProjectService(
        project_path=project_path,
        env_dir_path=get_env_dir_path(project_path),
    )


def setup_project(project_path, parent: QObject = None):
    global data_manager
    assert data_manager is None
    data_manager = ProjectDataManager(get_datafile_path(project_path), parent)

    global project_service
    assert project_service is None
    project_service = create_project_service(project_path)

    global tasks
    assert tasks is None
    tasks = BackgroundTasks(parent)

    global task_dispatcher
    assert task_dispatcher is None
    task_dispatcher = BackgroundTaskDispatcher(tasks)

    project_service.create_student_profile_if_not_exists()
