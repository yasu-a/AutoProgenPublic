from json import JSONDecodeError
from pathlib import Path

from domain.error import ProjectIOError
from domain.model.project import Project
from domain.model.value import ProjectID
from infra.io.files.project import ProjectCoreIO
from infra.path_layout import ProjectPathLayout


class ProjectRepository:
    def __init__(
            self,
            *,
            project_store_dir: Path,
            project_core_io: ProjectCoreIO,
    ):
        self._project_store_dir = project_store_dir
        self._project_core_io = project_core_io

    def _project_dir(self, project_id: ProjectID) -> Path:
        return self._project_store_dir / str(project_id)

    def list_ids(self) -> list[ProjectID]:
        self._project_store_dir.mkdir(parents=True, exist_ok=True)
        project_ids: list[ProjectID] = []
        for sub_folder_fullpath in self._project_store_dir.iterdir():
            if not sub_folder_fullpath.is_dir():
                continue
            folder_name = sub_folder_fullpath.name
            try:
                maybe_project_id = ProjectID(folder_name)
            except ValueError:
                continue
            project_ids.append(maybe_project_id)
        return project_ids

    def create_project_path_layout(self, project_id: ProjectID) -> ProjectPathLayout:
        return ProjectPathLayout(
            project_id=project_id,
            root=self._project_dir(project_id),
        )

    def get(self, project_id: ProjectID) -> Project:
        layout = self.create_project_path_layout(project_id)
        config_json_fullpath = layout.config_json

        if not config_json_fullpath.exists():
            raise ProjectIOError(f"Project \"{project_id!s}\" not found")

        try:
            json_body = self._project_core_io.read_json(
                project_id=project_id,
                json_fullpath=config_json_fullpath,
            )
        except (OSError, JSONDecodeError):
            raise ProjectIOError(f"Project \"{project_id!s}\" is not a valid project")

        try:
            project = Project.from_json(json_body)
        except (KeyError, IndexError, ValueError):
            raise ProjectIOError(f"Project \"{project_id!s}\" might be old")

        if project.project_id != project_id:
            raise ProjectIOError("Project name must be the same as folder name")

        return project

    def put(self, project: Project) -> None:
        layout = self.create_project_path_layout(project.project_id)
        if layout.config_json.exists():
            project_old = self.get(project.project_id)
            if project_old.project_id != project.project_id:
                raise ProjectIOError("Project id is unchangeable")
            if project_old.target_id != project.target_id:
                raise ProjectIOError("Target id is unchangeable")

        self._project_core_io.write_json(
            project_id=project.project_id,
            json_fullpath=layout.config_json,
            body=project.to_json(),
        )

    def delete(self, project_id: ProjectID) -> None:
        layout = self.create_project_path_layout(project_id)
        project_folder_fullpath = layout.root

        if not project_folder_fullpath.exists():
            raise ProjectIOError(f"Project \"{project_id!s}\" not found")

        self._project_core_io.rmtree_folder(
            project_id=project_id,
            path=project_folder_fullpath,
        )
