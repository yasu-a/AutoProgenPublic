from pathlib import Path

from domain.error import ManabaReportArchiveError
from domain.model.manaba_report_archive import ManabaReportArchive


class ManabaReportArchiveGateway:
    def read_from_path(self, *, archive_fullpath: Path) -> ManabaReportArchive:
        # ファイルシステム上のZIPを読み込み、ドメインモデルへ変換する。
        try:
            archive_bytes = archive_fullpath.read_bytes()
        except OSError as e:
            raise ManabaReportArchiveError(
                reason=f"提出アーカイブの読み込みに失敗しました。\n{e!s}",
            )
        return self.read_from_bytes(archive_bytes=archive_bytes)

    def read_from_bytes(self, *, archive_bytes: bytes) -> ManabaReportArchive:
        # メモリ上のZIP bytesからドメインモデルを構築する。
        return ManabaReportArchive(archive_bytes=archive_bytes)
