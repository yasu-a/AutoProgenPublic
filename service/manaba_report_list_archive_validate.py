from domain.error import ManabaReportListArchiveValidateServiceError
from domain.model.manaba_report_archive import ManabaReportArchive, ManabaSubmissionFolderPath
from domain.model.manaba_report_list import ManabaReportList


class ManabaReportListArchiveValidateService:
    def execute(
            self,
            *,
            report_list: ManabaReportList,
            archive: ManabaReportArchive,
    ) -> None:
        # reportlist 上の提出済みフォルダ集合を期待値として構築する。
        expected: set[ManabaSubmissionFolderPath] = set()
        for i in range(report_list.row_count()):
            row = report_list.get_row(row_index=i)
            if row.is_submitted and row.submission_folder_path is not None:
                expected.add(ManabaSubmissionFolderPath(row.submission_folder_path))

        # archive 実体から取得した提出フォルダ集合を実測値とする。
        actual = archive.get_submission_folder_paths()

        # reportlist にはあるが archive にはない提出フォルダを検出する。
        if expected - actual:
            raise ManabaReportListArchiveValidateServiceError(
                reason="提出アーカイブの提出フォルダに次の学生の提出フォルダが存在しません。\n"
                       + ", ".join(sorted(str(p.value) for p in (expected - actual))),
            )
        # archive にはあるが reportlist にはない提出フォルダを検出する。
        if actual - expected:
            raise ManabaReportListArchiveValidateServiceError(
                reason="提出アーカイブの提出フォルダに存在しないはずの提出フォルダが存在します。\n"
                       + ", ".join(sorted(str(p.value) for p in (actual - expected))),
            )
