import functools

from application.dependency.repository import get_global_settings_repository
from infra.task.manager import TaskManager


def create_task_manager() -> TaskManager:
    return TaskManager(
        global_settings_repo=get_global_settings_repository(),
    )


@functools.cache  # 互換ラッパー（移行完了後に削除予定）
def get_task_manager() -> TaskManager:
    return create_task_manager()
