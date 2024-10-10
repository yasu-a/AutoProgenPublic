from pathlib import Path

from application.state.current_project import get_current_project_id
from files.path_providers.project import ProjectListPathProvider, ProjectPathProvider
from files.path_providers.project_static import ProjectStaticPathProvider, \
    ReportSubmissionPathProvider


def get_project_list_folder_fullpath() -> Path:
    return Path("~/AutoProgenProjects").expanduser().resolve()


def get_project_list_path_provider():
    return ProjectListPathProvider(
        project_list_folder_fullpath=get_project_list_folder_fullpath(),
    )


def get_project_path_provider():
    return ProjectPathProvider(
        project_list_path_provider=get_project_list_path_provider(),
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
