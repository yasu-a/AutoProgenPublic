import functools
from pathlib import Path

from application.state.current_project import get_current_project_name
from files.global_path_provider import GlobalPathProvider
from files.project_path_provider import ProjectPathProviderWithoutDependency, ProjectPathProvider, \
    TestCasePathProvider, ReportPathProvider, StudentReportPathProvider, BuildPathProvider, \
    StudentBuildPathProvider, CompilePathProvider, StudentCompilePathProvider, ExecutePathProvider, \
    StudentExecutePathProvider, StudentTestCaseExecutePathProvider, TestPathProvider, \
    StudentTestPathProvider, StudentTestCaseTestPathProvider, StudentProgressPathProvider, \
    MarkPathProvider, StudentMarkPathProvider, TestSessionPathProvider


def get_project_list_folder_fullpath() -> Path:
    return Path("~/AutoProgenProjects").expanduser().resolve()


def get_current_project_fullpath() -> Path:
    project_name = get_current_project_name()
    assert project_name is not None, project_name
    return get_project_list_folder_fullpath() / str(project_name)


def get_project_path_provider_without_dependency(project_list_folder_fullpath: Path) \
        -> ProjectPathProviderWithoutDependency:
    # 特定のプロジェクトに依存しないProjectPathProvider
    # TODO: _without_dependency系クラスを解消せよ
    return ProjectPathProviderWithoutDependency(
        project_list_folder_fullpath=project_list_folder_fullpath,
    )


def get_global_path_provider() -> GlobalPathProvider:
    return GlobalPathProvider(
        global_settings_folder_fullpath=Path(".").resolve(),
    )


@functools.cache
def get_project_path_provider() -> ProjectPathProvider:
    return ProjectPathProvider(
        project_folder_fullpath=get_current_project_fullpath(),
    )


@functools.cache
def get_testcase_path_provider() -> TestCasePathProvider:
    return TestCasePathProvider(
        project_path_provider=get_project_path_provider(),
    )


@functools.cache
def get_report_path_provider() -> ReportPathProvider:
    return ReportPathProvider(
        project_path_provider=get_project_path_provider(),
    )


@functools.cache
def get_student_report_path_provider() -> StudentReportPathProvider:
    return StudentReportPathProvider(
        report_path_provider=get_report_path_provider(),
    )


@functools.cache
def get_build_path_provider() -> BuildPathProvider:
    return BuildPathProvider(
        project_path_provider=get_project_path_provider(),
    )


@functools.cache
def get_student_build_path_provider() -> StudentBuildPathProvider:
    return StudentBuildPathProvider(
        build_path_provider=get_build_path_provider(),
    )


@functools.cache
def get_compile_path_provider() -> CompilePathProvider:
    return CompilePathProvider(
        project_path_provider=get_project_path_provider(),
    )


@functools.cache
def get_student_compile_path_provider() -> StudentCompilePathProvider:
    return StudentCompilePathProvider(
        compile_path_provider=get_compile_path_provider(),
    )


@functools.cache
def get_execute_path_provider() -> ExecutePathProvider:
    return ExecutePathProvider(
        project_path_provider=get_project_path_provider(),
    )


@functools.cache
def get_student_execute_path_provider() -> StudentExecutePathProvider:
    return StudentExecutePathProvider(
        execute_path_provider=get_execute_path_provider(),
    )


@functools.cache
def get_student_testcase_execute_path_provider() -> StudentTestCaseExecutePathProvider:
    return StudentTestCaseExecutePathProvider(
        student_execute_path_provider=get_student_execute_path_provider(),
    )


@functools.cache
def get_test_path_provider() -> TestPathProvider:
    return TestPathProvider(
        project_path_provider=get_project_path_provider(),
    )


@functools.cache
def get_student_test_path_provider() -> StudentTestPathProvider:
    return StudentTestPathProvider(
        test_path_provider=get_test_path_provider(),
    )


@functools.cache
def get_student_testcase_test_path_provider() -> StudentTestCaseTestPathProvider:
    return StudentTestCaseTestPathProvider(
        student_test_path_provider=get_student_test_path_provider(),
    )


@functools.cache
def get_student_progress_path_provider() -> StudentProgressPathProvider:
    return StudentProgressPathProvider(
        student_build_path_provider=get_student_build_path_provider(),
        student_compile_path_provider=get_student_compile_path_provider(),
        student_execute_path_provider=get_student_execute_path_provider(),
        student_test_path_provider=get_student_test_path_provider(),
    )


@functools.cache
def get_mark_path_provider() -> MarkPathProvider:
    return MarkPathProvider(
        project_path_provider=get_project_path_provider(),
    )


@functools.cache
def get_student_mark_path_provider() -> StudentMarkPathProvider:
    return StudentMarkPathProvider(
        mark_path_provider=get_mark_path_provider(),
    )


@functools.cache
def get_test_session_path_provider() -> TestSessionPathProvider:
    return TestSessionPathProvider(
        project_path_provider=get_project_path_provider(),
    )
