import sys
from pathlib import Path

from application.state.current_project import get_current_project_id
from files.path_providers.current_project import DynamicPathProvider, StudentDynamicPathProvider, \
    StudentStageResultPathProvider, ProjectStaticPathProvider, ReportSubmissionPathProvider, \
    TestCaseConfigPathProvider, StudentMarkPathProvider, IOSessionPathProvider
from files.path_providers.global_ import GlobalPathProvider
from files.path_providers.project import ProjectListPathProvider, ProjectPathProvider


def get_global_path_provider():
    return GlobalPathProvider(
        global_settings_folder_fullpath=Path(sys.argv[0]).resolve().parent,
    )


def get_project_list_path_provider():
    return ProjectListPathProvider(
        project_list_folder_fullpath=Path("~/AutoProgenProjects").expanduser().resolve(),
    )


def get_project_path_provider():
    return ProjectPathProvider(
        project_list_path_provider=get_project_list_path_provider(),
    )


def get_testcase_config_path_provider():
    return TestCaseConfigPathProvider(
        current_project_id=get_current_project_id(),
        project_path_provider=get_project_path_provider(),
    )


def get_student_mark_path_provider():
    return StudentMarkPathProvider(
        current_project_id=get_current_project_id(),
        project_path_provider=get_project_path_provider(),
    )


def get_dynamic_path_provider():
    return DynamicPathProvider(
        current_project_id=get_current_project_id(),
        project_path_provider=get_project_path_provider(),
    )


def get_io_session_path_provider():
    return IOSessionPathProvider(
        dynamic_path_provider=get_dynamic_path_provider(),
    )


def get_student_dynamic_path_provider():
    return StudentDynamicPathProvider(
        dynamic_path_provider=get_dynamic_path_provider(),
    )


def get_student_stage_result_path_provider():
    return StudentStageResultPathProvider(
        student_dynamic_path_provider=get_student_dynamic_path_provider(),
    )


def get_project_static_path_provider():
    return ProjectStaticPathProvider(
        current_project_id=get_current_project_id(),
        project_path_provider=get_project_path_provider(),
    )


def get_report_submission_path_provider():
    return ReportSubmissionPathProvider(
        project_static_path_provider=get_project_static_path_provider(),
    )
