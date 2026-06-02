from pathlib import Path

from domain.error import ManabaReportArchiveError
from infra.gateway.manaba_report_archive import ManabaReportArchiveGateway


class ManabaReportArchiveValidateMasterExcelExistsUseCase:
    def __init__(self, *, manaba_report_archive_gateway: ManabaReportArchiveGateway) -> None:
        # ZIP読み込み責務は Gateway に委譲する。
        self._manaba_report_archive_gateway = manaba_report_archive_gateway

    def execute(self, manaba_report_archive_fullpath: Path) -> bool:
        # WELCOME 画面向けの軽量チェック。読めれば True、読めなければ False を返す。
        try:
            archive = self._manaba_report_archive_gateway.read_from_path(
                archive_fullpath=manaba_report_archive_fullpath,
            )
            _ = archive.read_report_list_excel_bytes()
            return True
        except (ManabaReportArchiveError, OSError):
            return False
