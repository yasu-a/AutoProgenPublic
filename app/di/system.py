# from functools import cache
# from pathlib import Path

# from app.di.path_config import get_path_config
# from app.di.state import get_current_project_id_state
# from shared.domain.interface.system import (
#     IGlobalCoreIO,
#     IProjectCoreIO,
#     ITaskManager,
#     ICurrentProjectCoreIO,
#     IManabaReportArchiveIO,
#     ICompileToolIO,
#     IExecutableIO,
#     IProjectDatabaseIO,
# )


# def get_global_core_io() -> IGlobalCoreIO:
#     from shared.infra.system.global_core_io import GlobalCoreIO
#     return GlobalCoreIO()


# def get_project_core_io() -> IProjectCoreIO:
#     from shared.infra.system.project_core_io import ProjectCoreIO
#     path_config = get_path_config()
#     return ProjectCoreIO(
#         project_folder_fullpath=path_config.project_folder_fullpath,
#     )


# def get_current_project_core_io() -> ICurrentProjectCoreIO:
#     from shared.infra.system.current_project_core_io import CurrentProjectCoreIO
#     return CurrentProjectCoreIO(
#         current_project_id=get_current_project_id_state().get(),
#         project_core_io=get_project_core_io(),
#     )


# def get_manaba_report_archive_io(manaba_report_archive_fullpath: Path) -> IManabaReportArchiveIO:
#     from shared.infra.system.report_archive import ManabaReportArchiveIO
#     return ManabaReportArchiveIO(
#         manaba_report_archive_fullpath=manaba_report_archive_fullpath,
#     )


# def get_compile_tool_io() -> ICompileToolIO:
#     from shared.infra.system.compile_tool import CompileToolIO
#     return CompileToolIO()


# def get_executable_io() -> IExecutableIO:
#     from shared.infra.system.executable import ExecutableIO
#     return ExecutableIO()


# def get_project_database_io() -> IProjectDatabaseIO:
#     from shared.infra.system.project_database import ProjectDatabaseIO
#     path_config = get_path_config()
#     current_project_id = get_current_project_id_state().get()
#     return ProjectDatabaseIO(
#         database_fullpath=path_config.current_project_database_fullpath(
#             current_project_id),
#     )


# @cache  # プロジェクト内共通インスタンス
# def get_task_manager() -> ITaskManager:
#     from shared.infra.system.task_manager import TaskManager
#     from app.di.repository import get_setting_repository
#     return TaskManager(
#         max_workers=get_setting_repository().get().max_workers,
#     )
