import functools

from application.dependency.repository import get_global_settings_repository
from infra.task.manager import TaskManager


@functools.cache  # プロジェクト内共通インスタンス
def get_task_manager() -> TaskManager:
    return TaskManager(
        global_settings_repo=get_global_settings_repository(),
    )
