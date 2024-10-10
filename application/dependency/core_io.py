from application.dependency.path_provider import get_project_path_provider
from application.state.current_project import get_current_project_id
from files.core.current_project import CurrentProjectCoreIO
from files.core.project import ProjectCoreIO


def get_project_core_io():
    return ProjectCoreIO(
        project_path_provider=get_project_path_provider(),
    )


def get_current_project_core_io():
    return CurrentProjectCoreIO(
        current_project_id=get_current_project_id(),
        project_core_io=get_project_core_io(),
    )
