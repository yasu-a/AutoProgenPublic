from pathlib import Path

from feature.export.usecase.interface import IScoreExportUseCase, WorksheetStat, ScoreExportResult
from shared.domain.entity.student_mark import StudentMarkEntity
from shared.domain.value.identifier import StudentID, TargetID


class ScoreExportUseCase(IScoreExportUseCase):
    def __init__(
            self,
            *,
            score_excel_io_factory: callable,  # Path -> ScoreExcelIO のファクトリー関数
    ):
        self._score_excel_io_factory = score_excel_io_factory

    def list_worksheet_stats(
            self,
            *,
            excel_fullpath: Path,
            student_ids: list[StudentID],
    ) -> list[WorksheetStat]:
        """ワークシートの状態一覧を取得"""
        score_excel_io = self._score_excel_io_factory(excel_fullpath)
        stats = score_excel_io.list_worksheet_stats(student_ids=student_ids)
        return [
            WorksheetStat(
                name=stat.name,
                valid=stat.valid,
                message=stat.message,
            )
            for stat in stats
        ]

    def has_data(
            self,
            *,
            excel_fullpath: Path,
            worksheet_name: str,
            student_ids: list[StudentID],
            target_id: TargetID,
    ) -> bool:
        """指定された位置にデータが存在するか"""
        score_excel_io = self._score_excel_io_factory(excel_fullpath)
        return score_excel_io.has_data(
            worksheet_name=worksheet_name,
            student_ids=student_ids,
            target_id=target_id,
        )

    def execute(
            self,
            *,
            excel_fullpath: Path,
            worksheet_name: str,
            student_marks: list[StudentMarkEntity],
            target_id: TargetID,
            do_backup: bool,
    ) -> ScoreExportResult:
        """点数をエクスポート"""
        try:
            score_excel_io = self._score_excel_io_factory(excel_fullpath)
            backup_path = score_excel_io.apply(
                worksheet_name=worksheet_name,
                student_marks=student_marks,
                target_id=target_id,
                do_backup=do_backup,
            )
            return ScoreExportResult(
                backup_path=backup_path,
                success=True,
                error_message=None,
            )
        except Exception as e:
            return ScoreExportResult(
                backup_path=None,
                success=False,
                error_message=str(e),
            )
