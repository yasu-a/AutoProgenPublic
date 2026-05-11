from infra.io.files.global_ import GlobalCoreIO
from infra.path_layout import AppPathLayout


class TestSourceRepository:
    # コンパイルテスト用のソースコードを取得するレポジトリ

    def __init__(
            self,
            *,
            app_path_layout: AppPathLayout,
            global_core_io: GlobalCoreIO,
    ):
        self._app_path_layout = app_path_layout
        self._global_core_io = global_core_io

    def get(self) -> bytes:
        source_file_fullpath = self._app_path_layout.compiler_test_source_file
        return self._global_core_io.read_file_content_bytes(
            file_fullpath=source_file_fullpath,
        )
