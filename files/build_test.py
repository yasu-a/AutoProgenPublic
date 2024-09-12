import uuid
from pathlib import Path

from app_logging import create_logger
from files.global_path_provider import GlobalPathProvider
from files.project_core import ProjectCoreIO
from files.project_path_provider import TestSessionPathProvider


class BuildTestIO:
    _logger = create_logger()

    def __init__(
            self,
            global_path_provider: GlobalPathProvider,
            test_session_path_provider: TestSessionPathProvider,
            project_core_io: ProjectCoreIO,
    ):
        self._global_path_provider = global_path_provider
        self._test_session_path_provider = test_session_path_provider
        self._project_core_io = project_core_io

    def create_session(self) -> uuid.UUID:  # session-id
        session_id = uuid.uuid4()
        test_folder_fullpath \
            = self._test_session_path_provider.test_session_folder_fullpath(str(session_id))
        test_folder_fullpath.mkdir(parents=True, exist_ok=True)
        return session_id

    def _put_test_source_file(self, session_id: uuid.UUID) -> None:
        test_source_file_fullpath \
            = self._global_path_provider.test_source_file_fullpath()
        test_folder_fullpath \
            = self._test_session_path_provider.test_session_folder_fullpath(str(session_id))
        test_folder_fullpath.mkdir(parents=True, exist_ok=True)
        self._project_core_io.copy_external_file_into_folder(
            src_file_fullpath=test_source_file_fullpath,
            dst_folder_fullpath=test_folder_fullpath,
        )

    def build(self, session_id: uuid.UUID) -> None:
        self._put_test_source_file(session_id)

    def get_compile_target_fullpath(self, session_id: uuid.UUID) -> Path:
        return self._test_session_path_provider.test_session_source_fullpath(str(session_id))

    def close_session(self, session_id: uuid.UUID) -> None:
        test_folder_fullpath \
            = self._test_session_path_provider.test_session_folder_fullpath(str(session_id))
        self._project_core_io.rmtree_folder(test_folder_fullpath)
