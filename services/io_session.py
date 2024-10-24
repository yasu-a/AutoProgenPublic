from domain.models.file_item import IOSessionFileItem, FullQualifiedIOSessionFileItemList, \
    FullQualifiedIOSessionFileItem
from domain.models.values import IOSessionID
from files.core.project import ProjectCoreIO
from files.path_providers.current_project import IOSessionPathProvider


class IOSessionRepository:
    def __init__(
            self,
            *,
            io_session_path_provider: IOSessionPathProvider,
            project_core_io: ProjectCoreIO,
    ):
        self._io_session_path_provider = io_session_path_provider
        self._project_core_io = project_core_io

    def create(self, io_session_id: IOSessionID) -> None:
        # IOセッションを生成する
        base_folder_fullpath = self._io_session_path_provider.base_folder_fullpath(io_session_id)
        base_folder_fullpath.mkdir(parents=True, exist_ok=False)
        return base_folder_fullpath

    def put(self, io_session_id: IOSessionID, file_item: IOSessionFileItem) -> None:
        # IOセッションにファイルを追加する
        base_folder_fullpath = self._io_session_path_provider.base_folder_fullpath(io_session_id)
        if not base_folder_fullpath.exists():
            raise ValueError(f"IO session {io_session_id} not found")

        file_fullpath = base_folder_fullpath / file_item.path
        file_fullpath.parent.mkdir(parents=True, exist_ok=True)
        self._project_core_io.write_file_content_bytes(
            file_fullpath=file_fullpath,
            content_bytes=file_item.content_bytes,
        )

    def list(self, io_session_id: IOSessionID) -> FullQualifiedIOSessionFileItemList:
        # IOセッションのファイルの一覧を取得する
        base_folder_fullpath = self._io_session_path_provider.base_folder_fullpath(io_session_id)
        if not base_folder_fullpath.exists():
            raise ValueError(f"IO session {io_session_id} not found")

        file_item_lst: list[FullQualifiedIOSessionFileItem] = []
        for path in base_folder_fullpath.rglob("**/*"):
            if path.is_file():
                content_bytes = self._project_core_io.read_file_content_bytes(
                    file_fullpath=path,
                )
                file_item_lst.append(
                    FullQualifiedIOSessionFileItem(
                        path=path.relative_to(base_folder_fullpath),
                        fullpath=path,
                        content_bytes=content_bytes,
                    ),
                )
        return FullQualifiedIOSessionFileItemList(file_item_lst)

    def delete(self, io_session_id: IOSessionID) -> None:
        # IOセッションを削除する
        base_folder_fullpath = self._io_session_path_provider.base_folder_fullpath(io_session_id)
        if not base_folder_fullpath.exists():
            raise ValueError(f"IO session {io_session_id} not found")
        self._project_core_io.rmtree_folder(base_folder_fullpath)
