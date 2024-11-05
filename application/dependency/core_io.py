from application.dependency.path_provider import *
from application.state.current_project import get_current_project_id
from infra.core.current_project import CurrentProjectCoreIO
from infra.core.global_ import GlobalCoreIO
from infra.core.project import ProjectCoreIO


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


