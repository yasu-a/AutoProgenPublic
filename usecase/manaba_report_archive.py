from pathlib import Path

from infra.io.report_archive import ManabaReportArchiveIO


class ManabaReportArchiveValidateMasterExcelExistsUseCase:
    def execute(self, manaba_report_archive_fullpath: Path) -> bool:
        # TODO: ManabaReportArchiveIO のパス依存を外し、コンテナから DI されたインスタンスを使える形へ移行する。
        return ManabaReportArchiveIO(
            manaba_report_archive_fullpath=manaba_report_archive_fullpath,
        ).validate_master_excel_exists()
