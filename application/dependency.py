import functools
from pathlib import Path

from application.current_project import get_current_project_name
from files.build_test import BuildTestIO
from files.compile_tool import CompileToolIO
from files.global_path_provider import GlobalPathProvider
from files.progress import ProgressIO
from files.project import ProjectIOWithoutDependency, ProjectIO
from files.project_core import ProjectCoreIO
from files.project_path_provider import ProjectPathProviderWithoutDependency, ProjectPathProvider
from files.report_archive import ManabaReportArchiveIO
from files.settings import GlobalSettingsIO
from files.testcase import TestCaseIO
from services.build import BuildService
from services.compile import CompileService
from services.compile_test import CompileTestService
from services.compiler_search import CompilerLocationSequentialSearchService
from services.execute import ExecuteService
from services.mark_snapshot import MarkSnapshotService
from services.project import ProjectService, ProjectConstructionService
from services.project_list import ProjectListService
from services.settings import GlobalSettingsEditService
from services.testcase_edit import TestCaseEditService
from tasks.manager import TaskManager


# プロジェクトに依存しないプロジェクト系
def get_project_path_provider_without_dependency(project_list_folder_fullpath: Path) \
        -> ProjectPathProviderWithoutDependency:
    # 特定のプロジェクトに依存しないProjectPathProvider
    # TODO: _without_dependency系クラスを解消せよ
    return ProjectPathProviderWithoutDependency(
        project_list_folder_fullpath=project_list_folder_fullpath,
    )


def get_project_io_without_dependency(project_list_folder_fullpath: Path) \
        -> ProjectIOWithoutDependency:
    # 特定のプロジェクトに依存しないProjectIO
    # TODO: _without_dependency系クラスを解消せよ
    return ProjectIOWithoutDependency(
        project_path_provider_without_dependency=get_project_path_provider_without_dependency(
            project_list_folder_fullpath=project_list_folder_fullpath,
        ),
    )


def get_project_list_service() -> ProjectListService:
    project_list_folder_fullpath = Path("~/AutoProgenProjects").expanduser().resolve()
    return ProjectListService(
        project_list_folder_fullpath=project_list_folder_fullpath,
        project_io_without_dependency=get_project_io_without_dependency(
            project_list_folder_fullpath=project_list_folder_fullpath,
        ),
    )


# Manabaレポートzipファイル


def get_manaba_report_archive_io(manaba_report_archive_fullpath: Path) -> ManabaReportArchiveIO:
    return ManabaReportArchiveIO(
        manaba_report_archive_fullpath=manaba_report_archive_fullpath,
    )


# グローバル


def get_global_path_provider() -> GlobalPathProvider:
    return GlobalPathProvider(
        global_settings_folder_fullpath=Path(".").resolve(),
    )


@functools.cache
def get_global_settings_io() -> GlobalSettingsIO:
    return GlobalSettingsIO(
        global_path_provider=get_global_path_provider(),
    )


def get_global_settings_edit_service() -> GlobalSettingsEditService:
    return GlobalSettingsEditService(
        global_settings_io=get_global_settings_io(),
    )


# タスクマネージャ


@functools.cache
def get_task_manager() -> TaskManager:
    return TaskManager(
        global_settings_io=get_global_settings_io(),
    )


# アクティブなプロジェクト


def get_current_project_fullpath() -> Path:
    project_name = get_current_project_name()
    assert project_name is not None, project_name
    return get_project_list_service().create_project_folder_fullpath(project_name)


@functools.cache
def get_project_path_provider() -> ProjectPathProvider:
    return ProjectPathProvider(
        project_folder_fullpath=get_current_project_fullpath(),
    )


@functools.cache
def get_project_core_io() -> ProjectCoreIO:
    return ProjectCoreIO(
        project_path_provider=get_project_path_provider(),
    )


@functools.cache
def get_project_io() -> ProjectIO:
    return ProjectIO(
        project_path_provider=get_project_path_provider(),
        project_core_io=get_project_core_io(),
    )


@functools.cache
def get_progress_io() -> ProgressIO:
    return ProgressIO(
        project_path_provider=get_project_path_provider(),
        project_core_io=get_project_core_io(),
        project_io=get_project_io(),
        testcase_io=get_testcase_io(),
    )


@functools.cache
def get_project_service() -> ProjectService:
    return ProjectService(
        project_io=get_project_io(),
        testcase_io=get_testcase_io(),
        progress_io=get_progress_io(),
    )


@functools.cache
def get_project_construction_service(
        *,
        manaba_report_archive_fullpath: Path,
) -> ProjectConstructionService:
    return ProjectConstructionService(
        project_path_provider=get_project_path_provider(),
        project_io=get_project_io(),
        manaba_report_archive_io=get_manaba_report_archive_io(
            manaba_report_archive_fullpath=manaba_report_archive_fullpath,
        )
    )


@functools.cache
def get_build_service() -> BuildService:
    return BuildService(
        project_io=get_project_io(),
        progress_io=get_progress_io(),
    )


@functools.cache
def get_compile_tool_io() -> CompileToolIO:
    return CompileToolIO()


def get_compile_service() -> CompileService:
    return CompileService(
        global_settings_io=get_global_settings_io(),
        project_io=get_project_io(),
        compile_tool_io=get_compile_tool_io(),
        progress_io=get_progress_io(),
    )


@functools.cache
def get_testcase_io() -> TestCaseIO:
    return TestCaseIO(
        project_path_provider=get_project_path_provider(),
        project_core_io=get_project_core_io(),
    )


@functools.cache
def get_testcase_edit_service() -> TestCaseEditService:
    return TestCaseEditService(
        testcase_io=get_testcase_io(),
    )


@functools.cache
def get_execute_service() -> ExecuteService:
    return ExecuteService(
        project_io=get_project_io(),
        testcase_io=get_testcase_io(),
        progress_io=get_progress_io(),
    )


# インスタンスごとのスコープなのでキャッシュしない
def get_compiler_location_search_service() -> CompilerLocationSequentialSearchService:
    return CompilerLocationSequentialSearchService()


@functools.cache
def get_build_test_io() -> BuildTestIO:
    return BuildTestIO(
        global_path_provider=get_global_path_provider(),
        project_path_provider=get_project_path_provider(),
        project_core_io=get_project_core_io(),
    )


@functools.cache
def get_compile_test_service() -> CompileTestService:
    return CompileTestService(
        global_settings_io=get_global_settings_io(),
        build_test_io=get_build_test_io(),
        compile_tool_io=get_compile_tool_io(),
    )


@functools.cache
def get_mark_snapshot_service() -> MarkSnapshotService:
    return MarkSnapshotService(
        project_io=get_project_io(),
        testcase_io=get_testcase_io(),
        progress_io=get_progress_io(),
    )
