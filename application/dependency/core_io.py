from application.dependency.path_provider import *
from application.state.current_project import require_current_project_id
from domain.model.value import ProjectID
from infra.io.files.current_project import CurrentProjectCoreIO
from infra.io.files.global_ import GlobalCoreIO
from infra.io.files.project import ProjectCoreIO


def get_global_core_io():
    return GlobalCoreIO()


def get_project_core_io():
    return ProjectCoreIO(
        project_path_provider=get_project_path_provider(),
    )


def create_current_project_core_io(project_id: ProjectID):
    return CurrentProjectCoreIO(
        current_project_id=project_id,
        project_core_io=get_project_core_io(),
    )


def get_current_project_core_io():
    return create_current_project_core_io(require_current_project_id())


