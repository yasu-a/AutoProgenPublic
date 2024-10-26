from pathlib import Path

from domain.models.storage import Storage, StorageFileContentMapper, StorageFileItem, \
    FileRelativePathListProducerType, FileContentMapperType, FileRelativePathExistsMapperType
from domain.models.values import StorageID
from files.core.current_project import CurrentProjectCoreIO
from files.path_providers.current_project import StoragePathProvider
from transaction import transactional_with


class StorageRepository:
    def __init__(
            self,
            *,
            storage_path_provider: StoragePathProvider,
            current_project_core_io: CurrentProjectCoreIO,
    ):
        self._storage_path_provider = storage_path_provider
        self._current_project_core_io = current_project_core_io

    def __get_file_relative_path_list_producer(self, base_folder_fullpath: Path) \
            -> FileRelativePathListProducerType:
        def file_relative_path_list_producer() -> list[Path]:
            file_fullpath_it = self._current_project_core_io.walk_files(
                folder_fullpath=base_folder_fullpath,
                return_absolute=False,
            )
            return list(file_fullpath_it)

        return file_relative_path_list_producer

    def __get_file_item_mapper(self, base_folder_fullpath: Path) \
            -> FileContentMapperType:
        def file_item_mapper(file_relative_path: Path, ) -> StorageFileItem | None:
            file_fullpath = base_folder_fullpath / file_relative_path
            if not file_relative_path.exists():
                return None
            content_bytes = self._current_project_core_io.read_file_content_bytes(
                file_fullpath=file_fullpath,
            )
            return StorageFileItem(
                relative_path=file_relative_path,
                content_bytes=content_bytes,
            )

        return file_item_mapper

    # noinspection PyMethodMayBeStatic
    def __get_file_relative_path_exists_mapper(self, base_folder_fullpath: Path) \
            -> FileRelativePathExistsMapperType:
        # TODO: この関数はself.__current_project_core_ioに依存しないのでPyMethodMayBeStatic警告が出る
        #       パスの存在の確認はpathlib.Path.existsで行っているが、これはCoreIOの責務ではないか
        def file_relative_path_exists_mapper(file_relative_path: Path) -> bool:
            file_fullpath = base_folder_fullpath / file_relative_path
            return file_fullpath.exists()

        return file_relative_path_exists_mapper

    @transactional_with("storge_id")
    def create(self, storage_id: StorageID) -> Storage:
        # ストレージを生成する
        base_folder_fullpath = self._storage_path_provider.base_folder_fullpath(storage_id)
        if base_folder_fullpath.exists():
            raise ValueError(f"IO session {storage_id} already exists")
        base_folder_fullpath.mkdir(parents=True, exist_ok=False)

        storage = Storage(
            storage_id=storage_id,
            base_folder_fullpath=base_folder_fullpath,
            files=StorageFileContentMapper(
                file_relative_path_list_producer=self.__get_file_relative_path_list_producer(
                    base_folder_fullpath,
                ),
                file_content_mapper=self.__get_file_item_mapper(
                    base_folder_fullpath,
                ),
                file_relative_path_exists_mapper=self.__get_file_relative_path_exists_mapper(
                    base_folder_fullpath,
                )
            )
        )
        return storage

    @transactional_with("storge_id")
    def get(self, storage_id: StorageID) -> Storage:
        # 既存のストレージを取得する

        base_folder_fullpath = self._storage_path_provider.base_folder_fullpath(
            storage_id,
        )
        if not base_folder_fullpath.exists():
            raise ValueError(f"IO session {storage_id} not found")

        storage = Storage(
            storage_id=storage_id,
            base_folder_fullpath=base_folder_fullpath,
            files=StorageFileContentMapper(
                file_relative_path_list_producer=self.__get_file_relative_path_list_producer(
                    base_folder_fullpath,
                ),
                file_content_mapper=self.__get_file_item_mapper(
                    base_folder_fullpath,
                ),
                file_relative_path_exists_mapper=self.__get_file_relative_path_exists_mapper(
                    base_folder_fullpath,
                )
            )
        )
        return storage

    @transactional_with(storge_id=lambda args: args["storage"].storage_id)
    def put(self, storage: Storage) -> None:
        # ストレージの変更をコミットする
        # ストレージにコミットした後のストレージインスタンスを操作してはならない！！！

        base_folder_fullpath = self._storage_path_provider.base_folder_fullpath(
            storage.storage_id,
        )
        if not base_folder_fullpath.exists():
            raise ValueError(f"IO session {storage.storage_id} not found")

        for file_relative_path, command in storage.files.iter_modifications():
            file_fullpath = base_folder_fullpath / file_relative_path
            command_type, updated_content = command
            if command_type == "deleted":
                self._current_project_core_io.unlink(
                    path=file_fullpath,
                )
            elif command_type == "updated":
                assert updated_content is not None
                self._current_project_core_io.write_file_content_bytes(
                    file_fullpath=file_fullpath,
                    content_bytes=updated_content,
                )
            else:
                assert False, command

    @transactional_with(storge_id=lambda args: args["storage"].storage_id)
    def delete(self, storage_id: StorageID) -> None:
        # ストレージを削除する

        base_folder_fullpath = self._storage_path_provider.base_folder_fullpath(
            storage_id,
        )
        if not base_folder_fullpath.exists():
            raise ValueError(f"IO session {storage_id} not found")

        self._current_project_core_io.rmtree_folder(
            path=base_folder_fullpath,
        )
