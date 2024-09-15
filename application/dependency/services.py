import functools
from pathlib import Path

from application.dependency.files import get_project_io_without_dependency, get_global_settings_io, \
    get_project_io, get_testcase_io, get_progress_io, get_manaba_report_archive_io, \
    get_compile_tool_io, get_build_test_io
from application.dependency.path_provider import get_project_path_provider, \
    get_student_report_path_provider, get_project_list_folder_fullpath
from services.build import BuildService
from services.compile import CompileService
from services.compile_test import CompileTestService
from services.compiler_search import CompilerLocationSequentialSearchService
from services.execute import ExecuteService
from services.progress import ProgressService
from services.project import ProjectService, ProjectCreateService
from services.project_list import ProjectListService
from services.settings import GlobalSettingsEditService
from services.snapshot import SnapshotService
from services.test import TestService
from services.testcase import TestCaseService


def get_project_list_service() -> ProjectListService:
    return ProjectListService(
        project_list_folder_fullpath=get_project_list_folder_fullpath(),
        project_io_without_dependency=get_project_io_without_dependency(
            project_list_folder_fullpath=get_project_list_folder_fullpath(),
        ),
    )


def get_global_settings_edit_service() -> GlobalSettingsEditService:
    return GlobalSettingsEditService(
        global_settings_io=get_global_settings_io(),
    )


@functools.cache
def get_project_service() -> ProjectService:
    return ProjectService(
        project_io=get_project_io(),
        testcase_io=get_testcase_io(),
        progress_io=get_progress_io(),
    )


@functools.cache
def get_project_create_service(
        *,
        manaba_report_archive_fullpath: Path,
) -> ProjectCreateService:
    return ProjectCreateService(
        project_path_provider=get_project_path_provider(),
        student_report_path_provider=get_student_report_path_provider(),
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
def get_compile_service() -> CompileService:
    return CompileService(
        global_settings_io=get_global_settings_io(),
        project_io=get_project_io(),
        compile_tool_io=get_compile_tool_io(),
        progress_io=get_progress_io(),
    )


@functools.cache
def get_testcase_service() -> TestCaseService:
    return TestCaseService(
        testcase_io=get_testcase_io(),
    )


@functools.cache
def get_execute_service() -> ExecuteService:
    return ExecuteService(
        project_io=get_project_io(),
        testcase_io=get_testcase_io(),
        progress_io=get_progress_io(),
    )


@functools.cache
def get_progress_service() -> ProgressService:
    return ProgressService(
        project_io=get_project_io(),
        testcase_io=get_testcase_io(),
        progress_io=get_progress_io(),
    )


@functools.cache
def get_test_service() -> TestService:
    return TestService(
        project_io=get_project_io(),
        testcase_io=get_testcase_io(),
        progress_io=get_progress_io(),
    )


def get_compiler_location_search_service() -> CompilerLocationSequentialSearchService:
    # インスタンスごとのスコープなのでキャッシュしない
    return CompilerLocationSequentialSearchService()


@functools.cache
def get_compile_test_service() -> CompileTestService:
    return CompileTestService(
        global_settings_io=get_global_settings_io(),
        build_test_io=get_build_test_io(),
        compile_tool_io=get_compile_tool_io(),
    )


@functools.cache
def get_mark_snapshot_service() -> SnapshotService:
    return SnapshotService(
        project_io=get_project_io(),
        testcase_io=get_testcase_io(),
        progress_io=get_progress_io(),
    )
