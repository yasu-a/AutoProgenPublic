from files.core.current_project import CurrentProjectCoreIO
from files.path_providers.global_ import GlobalPathProvider


class TestRunSourceRepository:
    # コンパイルテスト用のソースコードを取得するレポジトリ

    def __init__(
            self,
            *,
            global_path_provider: GlobalPathProvider,
            current_project_core_io: CurrentProjectCoreIO,
    ):
        self._global_path_provider = global_path_provider
        self._current_project_core_io = current_project_core_io

    def get(self) -> bytes:
        source_file_fullpath = self._global_path_provider.test_source_file_fullpath()
        return self._current_project_core_io.read_file_content_bytes(
            file_fullpath=source_file_fullpath,
        )
