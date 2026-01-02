from json import JSONDecodeError

from shared.domain.entity.project import ProjectEntity
from shared.domain.error import ProjectIOError
from shared.domain.interface.repository import IProjectRepository
from shared.domain.value.identifier import ProjectID
from shared.infra.path_provider.project import ProjectListPathProvider, ProjectPathProvider
from shared.infra.system.project_core_io import ProjectCoreIO


class ProjectRepository(IProjectRepository):
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

    def get(self, project_id: ProjectID) -> ProjectEntity:
        config_json_fullpath = self._project_path_provider.config_json_fullpath(project_id)

        if not config_json_fullpath.exists():
            raise ProjectIOError(f"ProjectEntity \"{project_id!s}\" not found")

        try:
            json_body = self._project_core_io.read_json(
                project_id=project_id,
                json_fullpath=config_json_fullpath,
            )
        except (OSError, JSONDecodeError):  # 失敗した場合は壊れているか古いバージョンのプロジェクトか
            raise ProjectIOError(f"ProjectEntity \"{project_id!s}\" is not a valid ProjectEntity")
        try:
            project_entity = ProjectEntity.from_json(json_body)
        except (KeyError, IndexError, ValueError):
            raise ProjectIOError(f"ProjectEntity \"{project_id!s}\" might be old")
        if project_entity.project_id != project_id:
            raise ProjectIOError(f"ProjectEntity name must be the same as folder name")

        return project_entity

    def put(self, project_entity: ProjectEntity) -> None:
        try:
            project_old = self.get(project_entity.project_id)
        except ProjectIOError:
            pass
        else:
            if project_old.project_id != project_entity.project_id:
                raise ProjectIOError(f"ProjectEntity id is unchangeable")
            if project_old.target_id != project_entity.target_id:
                raise ProjectIOError(f"Target id is unchangeable")

        config_json_fullpath = self._project_path_provider.config_json_fullpath(
            project_entity.project_id)

        self._project_core_io.write_json(
            project_id=project_entity.project_id,
            json_fullpath=config_json_fullpath,
            body=project_entity.to_json(),
        )

    def delete(self, project_id: ProjectID) -> None:
        project_folder_fullpath = self._project_path_provider.base_folder_fullpath(project_id)

        if not project_folder_fullpath.exists():
            raise ProjectIOError(f"ProjectEntity \"{project_id!s}\" not found")

        self._project_core_io.rmtree_folder(
            project_id=project_id,
            path=project_folder_fullpath,
        )
