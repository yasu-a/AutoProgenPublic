from pathlib import Path

from domain.model.value import StorageID
from infra.io.files.current_project import CurrentProjectCoreIO
from infra.path_provider.current_project import StoragePathProvider
from infra.path_provider.global_ import GlobalPathProvider
from util.app_logging import create_logger


class TestRunRepository:
    _logger = create_logger()

    def __init__(
            self,
            global_path_provider: GlobalPathProvider,
            storage_path_provider: StoragePathProvider,
            current_project_core_io: CurrentProjectCoreIO,
    ):
        self._global_path_provider = global_path_provider
        self._storage_path_provider = storage_path_provider
        self._current_project_core_io = current_project_core_io

    def create(self, test_run_id: StorageID) -> None:
        # テストセッションのフォルダを生成
        test_folder_fullpath = self._storage_path_provider.base_folder_fullpath(test_run_id)
        test_folder_fullpath.mkdir(parents=True, exist_ok=True)

        # テストセッション用のソースファイルを生成
        test_source_file_fullpath = self._global_path_provider.test_source_file_fullpath()
        test_folder_fullpath = self._storage_path_provider.base_folder_fullpath(test_run_id)
        test_folder_fullpath.mkdir(parents=True, exist_ok=True)
        self._current_project_core_io.copy_external_file_into_folder(
            src_file_fullpath=test_source_file_fullpath,
            dst_folder_fullpath=test_folder_fullpath,
        )

    def set_file(self, test_run_id: StorageID, filename: str, content: bytes) -> Path:
        test_session_folder_fullpath \
            = self._storage_path_provider.base_folder_fullpath(test_run_id)
        file_fullpath = test_session_folder_fullpath / filename
        self._current_project_core_io.write_file_content_bytes(
            file_fullpath=file_fullpath,
            content_bytes=content,
        )
        return file_fullpath

    def delete(self, test_run_id: StorageID) -> None:
        test_folder_fullpath = self._storage_path_provider.base_folder_fullpath(test_run_id)
        self._current_project_core_io.rmtree_folder(
            path=test_folder_fullpath,
        )
