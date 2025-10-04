from json import JSONDecodeError

from domain.error import ProjectIOError
from domain.model.project import Project
from domain.model.value import ProjectID
from infra.io.files.project import ProjectCoreIO
from infra.path_provider.project import ProjectListPathProvider, ProjectPathProvider


class ProjectRepository:
    def __init__(
            self,
            *,
            project_list_path_provider: ProjectListPathProvider,
            project_path_provider: ProjectPathProvider,
            project_core_io: ProjectCoreIO,
    ):
        self._project_list_path_provider = project_list_path_provider
        self._project_path_provider = project_path_provider
        self._project_core_io = project_core_io

    def get(self, project_id: ProjectID) -> Project:
        config_json_fullpath = self._project_path_provider.config_json_fullpath(project_id)

        if not config_json_fullpath.exists():
            raise ProjectIOError(f"Project \"{project_id!s}\" not found")

        try:
            json_body = self._project_core_io.read_json(
                project_id=project_id,
                json_fullpath=config_json_fullpath,
            )
        except (OSError, JSONDecodeError):  # 失敗した場合は壊れているか古いバージョンのプロジェクトか
            raise ProjectIOError(f"Project \"{project_id!s}\" is not a valid project")
        try:
            project = Project.from_json(json_body)
        except (KeyError, IndexError, ValueError):
            raise ProjectIOError(f"Project \"{project_id!s}\" might be old")
        if project.project_id != project_id:
            raise ProjectIOError(f"Project name must be the same as folder name")

        return project

    def put(self, project: Project) -> None:
        try:
            project_old = self.get(project.project_id)
        except ProjectIOError:
            pass
        else:
            if project_old.project_id != project.project_id:
                raise ProjectIOError(f"Project id is unchangeable")
            if project_old.target_id != project.target_id:
                raise ProjectIOError(f"Target id is unchangeable")

        config_json_fullpath = self._project_path_provider.config_json_fullpath(project.project_id)

        project = self._project_core_io.write_json(
            project_id=project.project_id,
            json_fullpath=config_json_fullpath,
            body=project.to_json(),
        )
        return project

    def delete(self, project_id: ProjectID) -> None:
        project_folder_fullpath = self._project_path_provider.base_folder_fullpath(project_id)

        if not project_folder_fullpath.exists():
            raise ProjectIOError(f"Project \"{project_id!s}\" not found")

        self._project_core_io.rmtree_folder(
            project_id=project_id,
            path=project_folder_fullpath,
        )
