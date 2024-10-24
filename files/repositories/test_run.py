from pathlib import Path

from app_logging import create_logger
from domain.models.values import IOSessionID
from files.core.current_project import CurrentProjectCoreIO
from files.path_providers.current_project import IOSessionPathProvider
from files.path_providers.global_ import GlobalPathProvider


class TestRunRepository:
    _logger = create_logger()

    def __init__(
            self,
            global_path_provider: GlobalPathProvider,
            io_session_path_provider: IOSessionPathProvider,
            current_project_core_io: CurrentProjectCoreIO,
    ):
        self._global_path_provider = global_path_provider
        self._io_session_path_provider = io_session_path_provider
        self._current_project_core_io = current_project_core_io

    def create(self, test_run_id: IOSessionID) -> None:
        # テストセッションのフォルダを生成
        test_folder_fullpath = self._io_session_path_provider.base_folder_fullpath(test_run_id)
        test_folder_fullpath.mkdir(parents=True, exist_ok=True)

        # テストセッション用のソースファイルを生成
        test_source_file_fullpath = self._global_path_provider.test_source_file_fullpath()
        test_folder_fullpath = self._io_session_path_provider.base_folder_fullpath(test_run_id)
        test_folder_fullpath.mkdir(parents=True, exist_ok=True)
        self._current_project_core_io.copy_external_file_into_folder(
            src_file_fullpath=test_source_file_fullpath,
            dst_folder_fullpath=test_folder_fullpath,
        )

    def set_file(self, test_run_id: IOSessionID, filename: str, content: bytes) -> Path:
        test_session_folder_fullpath \
            = self._io_session_path_provider.base_folder_fullpath(test_run_id)
        file_fullpath = test_session_folder_fullpath / filename
        self._current_project_core_io.write_file_content_bytes(
            file_fullpath=file_fullpath,
            content_bytes=content,
        )
        return file_fullpath

    def delete(self, test_run_id: IOSessionID) -> None:
        test_folder_fullpath = self._io_session_path_provider.base_folder_fullpath(test_run_id)
        self._current_project_core_io.rmtree_folder(
            path=test_folder_fullpath,
        )
