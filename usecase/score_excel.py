from pathlib import Path

from domain.model.student_mark import StudentMark
from domain.model.value import StudentID, TargetID
from infra.io.score_excel import ScoreExcelIO, WorksheetStat


class ScoreExcelListWorksheetStatsUseCase:
    def execute(self, *, excel_fullpath: Path, student_ids: list[StudentID]) -> list[WorksheetStat]:
        # TODO: ScoreExcelIO のパス依存を外し、コンテナから DI されたインスタンスを使える形へ移行する。
        return ScoreExcelIO(excel_fullpath=excel_fullpath).list_worksheet_stats(
            student_ids=student_ids,
        )


class ScoreExcelHasDataUseCase:
    def execute(
            self,
            *,
            excel_fullpath: Path,
            worksheet_name: str,
            student_ids: list[StudentID],
            target_id: TargetID,
    ) -> bool:
        # TODO: ScoreExcelIO のパス依存を外し、コンテナから DI されたインスタンスを使える形へ移行する。
        return ScoreExcelIO(excel_fullpath=excel_fullpath).has_data(
            worksheet_name=worksheet_name,
            student_ids=student_ids,
            target_id=target_id,
        )


class ScoreExcelApplyUseCase:
    def execute(
            self,
            *,
            excel_fullpath: Path,
            worksheet_name: str,
            student_marks: list[StudentMark],
            target_id: TargetID,
            do_backup: bool,
    ) -> Path | None:
        # TODO: ScoreExcelIO のパス依存を外し、コンテナから DI されたインスタンスを使える形へ移行する。
        return ScoreExcelIO(excel_fullpath=excel_fullpath).apply(
            worksheet_name=worksheet_name,
            student_marks=student_marks,
            target_id=target_id,
            do_backup=do_backup,
        )
