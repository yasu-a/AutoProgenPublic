import functools

from application.dependency.files import get_global_settings_io
from tasks.manager import TaskManager


@functools.cache
def get_task_manager() -> TaskManager:
    return TaskManager(
        global_settings_io=get_global_settings_io(),
    )
