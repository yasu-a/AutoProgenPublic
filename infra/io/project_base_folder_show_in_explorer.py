import os

from domain.model.value import ProjectID
from infra.path_provider.project import ProjectListPathProvider


class ProjectFolderShowInExplorerIO:
    # プロジェクトの各種フォルダをエクスプローラで開く

    def __init__(
            self,
            *,
            project_list_path_provider: ProjectListPathProvider,
    ):
        self._project_list_path_provider = project_list_path_provider

    def show_base_folder(self) -> None:
        # プロジェクトの管理フォルダをエクスプローラで開く
        base_folder_fullpath = self._project_list_path_provider.base_folder_fullpath()
        if base_folder_fullpath.exists():
            os.startfile(base_folder_fullpath)

    def show_folder(self, project_id: ProjectID) -> None:
        # プロジェクトの場所をエクスプローラで開く
        project_folder_fullpath \
            = self._project_list_path_provider.project_folder_fullpath(project_id)
        if project_folder_fullpath.exists():
            os.startfile(project_folder_fullpath)
