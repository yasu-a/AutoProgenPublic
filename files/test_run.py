from pathlib import Path

from app_logging import create_logger
from domain.models.values import IOSessionID
from files.core.project import ProjectCoreIO
from files.path_providers.global_ import GlobalPathProvider
from files.path_providers.project_dynamic import TestRunPathProvider


class TestRunRepository:
    _logger = create_logger()

    def __init__(
            self,
            global_path_provider: GlobalPathProvider,
            test_run_path_provider: TestRunPathProvider,
            project_core_io: ProjectCoreIO,
    ):
        self._global_path_provider = global_path_provider
        self._test_run_path_provider = test_run_path_provider
        self._project_core_io = project_core_io

    def create(self, test_run_id: IOSessionID) -> None:
        # テストセッションのフォルダを生成
        test_folder_fullpath = self._test_run_path_provider.base_folder_fullpath(test_run_id)
        test_folder_fullpath.mkdir(parents=True, exist_ok=True)

        # テストセッション用のソースファイルを生成
        test_source_file_fullpath = self._global_path_provider.test_source_file_fullpath()
        test_folder_fullpath = self._test_run_path_provider.base_folder_fullpath(test_run_id)
        test_folder_fullpath.mkdir(parents=True, exist_ok=True)
        self._project_core_io.copy_external_file_into_folder(
            src_file_fullpath=test_source_file_fullpath,
            dst_folder_fullpath=test_folder_fullpath,
        )

    def set_file(self, test_run_id: IOSessionID, filename: str, content: bytes) -> Path:
        test_session_folder_fullpath \
            = self._test_run_path_provider.base_folder_fullpath(test_run_id)
        file_fullpath = test_session_folder_fullpath / filename
        self._project_core_io.write_file_content_bytes(
            file_fullpath=file_fullpath,
            content_bytes=content,
        )
        return file_fullpath

    def delete(self, test_run_id: IOSessionID) -> None:
        test_folder_fullpath = self._test_run_path_provider.base_folder_fullpath(test_run_id)
        self._project_core_io.rmtree_folder(test_folder_fullpath)
