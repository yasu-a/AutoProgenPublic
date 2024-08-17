import shutil
import uuid
from pathlib import Path

from app_logging import create_logger
from files.global_path_provider import GlobalPathProvider
from files.project_path_provider import ProjectPathProvider


class BuildTestIO:
    _logger = create_logger()

    def __init__(
            self,
            global_path_provider: GlobalPathProvider,
            project_path_provider: ProjectPathProvider,
    ):
        self._global_path_provider = global_path_provider
        self._project_path_provider = project_path_provider

    # TODO: move into ProjectCoreIO and share it with other IO classes
    def _rmtree(self, path: Path) -> None:
        # プロジェクト内のフォルダを削除する
        assert path.is_absolute(), path
        assert path.is_relative_to(
            self._project_path_provider.project_folder_fullpath()
        ), path
        self._logger.info(f"rmtree {path!s}")
        shutil.rmtree(path)

    # TODO: move into ProjectCoreIO and share it with other IO classes
    def _copy_external_file_into_folder(
            self,
            src_file_fullpath: Path,
            dst_folder_fullpath: Path,
            dst_file_name: str = None,
    ) -> None:
        # 任意のファイルをプロジェクト内のフォルダにコピーする
        assert src_file_fullpath.is_absolute(), src_file_fullpath
        assert src_file_fullpath.is_file(), src_file_fullpath
        assert dst_folder_fullpath.is_absolute(), dst_folder_fullpath
        assert dst_folder_fullpath.is_relative_to(
            self._project_path_provider.project_folder_fullpath()
        ), dst_folder_fullpath
        assert dst_folder_fullpath.is_dir(), dst_folder_fullpath
        if dst_file_name is None:
            dst_file_name = src_file_fullpath.name
        shutil.copy(src_file_fullpath, dst_folder_fullpath / dst_file_name)

    def create_session(self) -> uuid.UUID:  # session-id
        session_id = uuid.uuid4()
        test_folder_fullpath \
            = self._project_path_provider.test_session_folder_fullpath(str(session_id))
        test_folder_fullpath.mkdir(parents=True, exist_ok=True)
        return session_id

    def _put_test_source_file(self, session_id: uuid.UUID) -> None:
        test_source_file_fullpath \
            = self._global_path_provider.test_source_file_fullpath()
        test_folder_fullpath \
            = self._project_path_provider.test_session_folder_fullpath(str(session_id))
        test_folder_fullpath.mkdir(parents=True, exist_ok=True)
        self._copy_external_file_into_folder(
            src_file_fullpath=test_source_file_fullpath,
            dst_folder_fullpath=test_folder_fullpath,
        )

    def build(self, session_id: uuid.UUID) -> None:
        self._put_test_source_file(session_id)

    def get_compile_target_fullpath(self, session_id: uuid.UUID) -> Path:
        return self._project_path_provider.test_session_source_fullpath(str(session_id))

    def close_session(self, session_id: uuid.UUID) -> None:
        test_folder_fullpath \
            = self._project_path_provider.test_session_folder_fullpath(str(session_id))
        self._rmtree(test_folder_fullpath)
