from application.dependency.core_io import *
from application.dependency.path_provider import *
from files.repositories.project import ProjectRepository
from files.repositories.student import StudentRepository


def get_project_repository():
    return ProjectRepository(
        project_list_path_provider=get_project_list_path_provider(),
        project_path_provider=get_project_path_provider(),
        project_core_io=get_project_core_io(),
    )


def get_student_repository():
    return StudentRepository(
        project_static_path_provider=get_project_static_path_provider(),
        current_project_core_io=get_current_project_core_io(),
    )
