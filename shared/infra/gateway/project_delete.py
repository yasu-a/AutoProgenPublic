from shared.domain.error import ProjectIOError
from shared.domain.interface.gateway import IProjectDeleteGateway
from shared.domain.interface.path_manager import IAppPathManager
from shared.domain.value.identifier import ProjectID
from shared.infra.system.project_core_io import ProjectCoreIOFactory


class ProjectDeleteGateway(IProjectDeleteGateway):
    def __init__(
            self,
            app_path_manager: IAppPathManager,
            project_core_io_factory: ProjectCoreIOFactory,
    ):
        self._app_path_manager = app_path_manager
        self._project_core_io_factory = project_core_io_factory

    def delete_project(self, project_id: ProjectID) -> None:
        project_folder_fullpath = self._app_path_manager.get_project_dir(project_id)

        if not project_folder_fullpath.exists():
            raise ProjectIOError(f"ProjectEntity \"{project_id!s}\" not found")

        self._project_core_io_factory.create_project_core_io(
            project_id=project_id,
        ).rmtree_folder(
            path=project_folder_fullpath,
        )
