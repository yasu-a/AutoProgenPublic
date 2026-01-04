from functools import cache

from app.di.path_config import *
from app.di.state import get_current_project_id_state
from shared.infra.system.compile_tool import CompileToolIO
from shared.infra.system.current_project_core_io import CurrentProjectCoreIO
from shared.infra.system.executable import ExecutableIO
from shared.infra.system.global_core_io import GlobalCoreIO
from shared.infra.system.project_core_io import ProjectCoreIO
from shared.infra.system.project_database import ProjectDatabaseIO
from shared.infra.system.report_archive import ManabaReportArchiveIO
from shared.infra.system.task_manager import TaskManager


def get_global_core_io():
    return GlobalCoreIO()


def get_project_core_io():
    path_config = get_path_config()
    return ProjectCoreIO(
        project_folder_fullpath=path_config.project_folder_fullpath,
    )


def get_current_project_core_io():
    return CurrentProjectCoreIO(
        current_project_id=get_current_project_id_state().get(),
        project_core_io=get_project_core_io(),
    )


def get_manaba_report_archive_io(manaba_report_archive_fullpath: Path):
    return ManabaReportArchiveIO(
        manaba_report_archive_fullpath=manaba_report_archive_fullpath,
    )


def get_compile_tool_io():
    return CompileToolIO()


def get_executable_io():
    return ExecutableIO()


def get_project_database_io():
    path_config = get_path_config()
    current_project_id = get_current_project_id_state().get()
    return ProjectDatabaseIO(
        database_fullpath=path_config.current_project_database_fullpath(current_project_id),
    )


@cache  # プロジェクト内共通インスタンス
def get_task_manager() -> TaskManager:
    from app.di.repository import get_setting_repository
    return TaskManager(
        max_workers=get_setting_repository().get().max_workers,
    )
