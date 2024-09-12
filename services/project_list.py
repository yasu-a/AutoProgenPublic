from datetime import datetime
from pathlib import Path

from app_logging import create_logger
from domain.models.project_stat import ProjectStat
from domain.models.values import ProjectName
from files.project import ProjectIOWithoutDependency


class ProjectListService:
    _logger = create_logger()

    def __init__(
            self,
            project_list_folder_fullpath: Path,
            project_io_without_dependency: ProjectIOWithoutDependency,
    ):
        self._base_fullpath = project_list_folder_fullpath
        self._project_io_without_dependency = project_io_without_dependency

    def _ensure_exists_base(self):
        self._logger.debug(str(self._base_fullpath))
        self._base_fullpath.mkdir(parents=True, exist_ok=True)

    def name_exists(self, name: ProjectName) -> bool:
        self._ensure_exists_base()

        for child_dir_fullpath in self._base_fullpath.iterdir():
            if child_dir_fullpath.name == str(name):
                return True
        return False

    def list_project_stats(self) -> list[ProjectStat]:
        stats = []
        for project_fullpath in self._base_fullpath.iterdir():
            project_name = ProjectName(project_fullpath.name)
            project_config = self._project_io_without_dependency.read_config(project_name)
            if project_config is None:
                continue
            stat = ProjectStat(
                project_name=project_name,
                target_id=project_config.target_id,
                mtime=datetime.fromtimestamp(project_fullpath.stat().st_mtime),
            )
            stats.append(stat)
        return sorted(stats, reverse=True)
