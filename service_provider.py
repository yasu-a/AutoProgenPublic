import functools
from pathlib import Path

from domain.models.values import ProjectName
from files.build_test import BuildTestIO
from files.compile_tool import CompileToolIO
from files.global_path_provider import GlobalPathProvider
from files.project import ProjectIO, ProjectIOWithoutDependency
from files.project_path_provider import ProjectPathProvider, ProjectPathProviderWithoutDependency
from files.report_archive import ManabaReportArchiveIO
from files.settings import GlobalSettingsIO
from files.testcase import TestCaseIO
from services.build import BuildService
from services.compile import CompileService
from services.compile_test import CompileTestService
from services.compiler_search import CompilerLocationSequentialSearchService
from services.execute import ExecuteService
from services.project import ProjectService, ProjectConstructionService
from services.project_list import ProjectListService
from services.settings import GlobalSettingsEditService
from services.testcase_edit import TestCaseEditService
from tasks.manager import TaskManager

_debug = False


def set_debug(debug: bool):
    global _debug
    _debug = debug


def is_debug() -> bool:
    return _debug


def get_project_path_provider_without_dependency(project_list_folder_fullpath: Path) \
        -> ProjectPathProviderWithoutDependency:
    return ProjectPathProviderWithoutDependency(
        project_list_folder_fullpath=project_list_folder_fullpath,
    )


def get_project_io_without_dependency(project_list_folder_fullpath: Path) \
        -> ProjectIOWithoutDependency:
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


def get_manaba_report_archive_io(manaba_report_archive_fullpath: Path) -> ManabaReportArchiveIO:
    return ManabaReportArchiveIO(
        manaba_report_archive_fullpath=manaba_report_archive_fullpath,
    )


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


_project_name: ProjectName | None = None


def set_project_name(project_name: ProjectName):
    global _project_name
    assert _project_name is None, _project_name
    _project_name = project_name


def _get_project_fullpath() -> Path:
    assert _project_name is not None, _project_name
    return get_project_list_service().create_project_folder_fullpath(_project_name)


@functools.cache
def get_task_manager() -> TaskManager:
    return TaskManager(
        global_settings_io=get_global_settings_io(),
    )


@functools.cache
def get_project_path_provider() -> ProjectPathProvider:
    return ProjectPathProvider(
        project_folder_fullpath=_get_project_fullpath(),
    )


@functools.cache
def get_project_io() -> ProjectIO:
    return ProjectIO(
        project_path_provider=get_project_path_provider(),
    )


@functools.cache
def get_project_service() -> ProjectService:
    return ProjectService(
        project_io=get_project_io(),
        testcase_io=get_testcase_io(),
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
    )


@functools.cache
def get_compile_tool_io() -> CompileToolIO:
    return CompileToolIO()


def get_compile_service() -> CompileService:
    return CompileService(
        global_settings_io=get_global_settings_io(),
        project_io=get_project_io(),
        compile_tool_io=get_compile_tool_io(),
    )


@functools.cache
def get_testcase_io() -> TestCaseIO:
    return TestCaseIO(
        project_path_provider=get_project_path_provider(),
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
    )


def get_compiler_location_search_service() -> CompilerLocationSequentialSearchService:
    return CompilerLocationSequentialSearchService()


def get_build_test_io() -> BuildTestIO:
    return BuildTestIO(
        global_path_provider=get_global_path_provider(),
        project_path_provider=get_project_path_provider(),
    )


@functools.cache
def get_compile_test_service() -> CompileTestService:
    return CompileTestService(
        global_settings_io=get_global_settings_io(),
        build_test_io=get_build_test_io(),
        compile_tool_io=get_compile_tool_io(),
    )
