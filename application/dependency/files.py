import functools
from pathlib import Path

from application.dependency.path_provider import get_project_path_provider_without_dependency, \
    get_global_path_provider, get_project_path_provider, get_testcase_path_provider, \
    get_student_compile_path_provider, get_student_testcase_execute_path_provider, \
    get_student_build_path_provider, get_student_execute_path_provider, \
    get_student_test_path_provider, get_student_report_path_provider, \
    get_student_progress_path_provider, get_student_mark_path_provider, \
    get_test_session_path_provider
from files.build_test import BuildTestIO
from files.compile_tool import CompileToolIO
from files.progress import ProgressIO
from files.project import ProjectIOWithoutDependency, ProjectIO
from files.project_core import ProjectCoreIO
from files.report_archive import ManabaReportArchiveIO
from files.settings import GlobalSettingsIO
from files.testcase import TestCaseIO


def get_project_io_without_dependency(project_list_folder_fullpath: Path) \
        -> ProjectIOWithoutDependency:
    # 特定のプロジェクトに依存しないProjectIO
    # TODO: _without_dependency系クラスを解消せよ
    return ProjectIOWithoutDependency(
        project_path_provider_without_dependency=get_project_path_provider_without_dependency(
            project_list_folder_fullpath=project_list_folder_fullpath,
        ),
    )


def get_manaba_report_archive_io(manaba_report_archive_fullpath: Path) -> ManabaReportArchiveIO:
    return ManabaReportArchiveIO(
        manaba_report_archive_fullpath=manaba_report_archive_fullpath,
    )


@functools.cache
def get_global_settings_io() -> GlobalSettingsIO:
    return GlobalSettingsIO(
        global_path_provider=get_global_path_provider(),
    )


@functools.cache
def get_testcase_io() -> TestCaseIO:
    return TestCaseIO(
        project_path_provider=get_project_path_provider(),
        testcase_path_provider=get_testcase_path_provider(),
        student_compile_path_provider=get_student_compile_path_provider(),
        student_testcase_execute_path_provider=get_student_testcase_execute_path_provider(),
        project_core_io=get_project_core_io(),
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
        student_build_path_provider=get_student_build_path_provider(),
        student_compile_path_provider=get_student_compile_path_provider(),
        student_execute_path_provider=get_student_execute_path_provider(),
        student_test_path_provider=get_student_test_path_provider(),
        student_report_path_provider=get_student_report_path_provider(),
        project_core_io=get_project_core_io(),
    )


@functools.cache
def get_progress_io() -> ProgressIO:
    return ProgressIO(
        project_path_provider=get_project_path_provider(),
        student_progress_path_provider=get_student_progress_path_provider(),
        student_build_path_provider=get_student_build_path_provider(),
        student_compile_path_provider=get_student_compile_path_provider(),
        student_execute_path_provider=get_student_execute_path_provider(),
        student_test_path_provider=get_student_test_path_provider(),
        student_mark_path_provider=get_student_mark_path_provider(),
        project_core_io=get_project_core_io(),
        project_io=get_project_io(),
        testcase_io=get_testcase_io(),
    )


@functools.cache
def get_compile_tool_io() -> CompileToolIO:
    return CompileToolIO()


@functools.cache
def get_build_test_io() -> BuildTestIO:
    return BuildTestIO(
        global_path_provider=get_global_path_provider(),
        test_session_path_provider=get_test_session_path_provider(),
        project_core_io=get_project_core_io(),
    )
