import os
from pathlib import Path

from domain.model.value import ProjectID


class ProjectFolderShowInExplorerIO:
    # プロジェクトの各種フォルダをエクスプローラで開く

    def __init__(
            self,
            *,
            project_store_dir: Path,
    ):
        self._project_store_dir = project_store_dir

    def show_base_folder(self) -> None:
        # プロジェクトの管理フォルダをエクスプローラで開く
        base_folder_fullpath = self._project_store_dir
        if base_folder_fullpath.exists():
            os.startfile(base_folder_fullpath)

    def show_folder(self, project_id: ProjectID) -> None:
        # プロジェクトの場所をエクスプローラで開く
        project_folder_fullpath = self._project_store_dir / str(project_id)
        if project_folder_fullpath.exists():
            os.startfile(project_folder_fullpath)
