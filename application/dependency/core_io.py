from application.dependency.path_provider import *
from application.state.current_project import get_current_project_id
from files.core.current_project import CurrentProjectCoreIO
from files.core.global_ import GlobalCoreIO
from files.core.project import ProjectCoreIO
from files.external.student_folder_show_in_explorer import \
    StudentFolderShowInExplorerIO


def get_global_core_io():
    return GlobalCoreIO()


def get_project_core_io():
    return ProjectCoreIO(
        project_path_provider=get_project_path_provider(),
    )


def get_current_project_core_io():
    return CurrentProjectCoreIO(
        current_project_id=get_current_project_id(),
        project_core_io=get_project_core_io(),
    )


def get_student_folder_show_in_explorer_io():
    return StudentFolderShowInExplorerIO(
        student_submission_path_provider=get_student_submission_path_provider(),
    )
