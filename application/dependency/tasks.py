import functools

from application.dependency.repositories import get_global_config_repository
from tasks.manager import TaskManager


@functools.cache
def get_task_manager() -> TaskManager:
    return TaskManager(
        global_settings_repo=get_global_config_repository(),
    )
