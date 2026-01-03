from shared.domain.interface.repository import ITestSourceRepository
from shared.infra.path_provider.global_ import GlobalPathProvider
from shared.infra.system.global_core_io import GlobalCoreIO


class TestSourceRepository(ITestSourceRepository):
    # コンパイルテスト用のソースコードを取得するレポジトリ

    def __init__(
            self,
            *,
            global_path_provider: GlobalPathProvider,
            global_core_io: GlobalCoreIO,
    ):
        self._global_path_provider = global_path_provider
        self._global_core_io = global_core_io

    def get(self) -> bytes:
        source_file_fullpath = self._global_path_provider.test_source_file_fullpath()
        return self._global_core_io.read_file_content_bytes(
            file_fullpath=source_file_fullpath,
        )
