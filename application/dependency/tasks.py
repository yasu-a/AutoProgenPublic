import functools

from application.dependency.repositories import get_global_config_repository
from infra.tasks.manager import TaskManager


@functools.cache  # プロジェクト内共通インスタンス
def get_task_manager() -> TaskManager:
    return TaskManager(
        global_settings_repo=get_global_config_repository(),
    )
