from pathlib import Path

from shared.domain.interface.repository import ITestSourceRepository
from shared.infra.system.global_core_io import GlobalCoreIO


class TestSourceRepository(ITestSourceRepository):
    # コンパイルテスト用のソースコードを取得するレポジトリ

    def __init__(
            self,
            *,
            test_source_file_fullpath: Path,
            global_core_io: GlobalCoreIO,
    ):
        self._test_source_file_fullpath = test_source_file_fullpath
        self._global_core_io = global_core_io

    def get(self) -> bytes:
        return self._global_core_io.read_file_content_bytes(
            file_fullpath=self._test_source_file_fullpath,
        )
