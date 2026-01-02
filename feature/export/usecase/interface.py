from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from feature.export.domain.interface.system import WorksheetStat
from shared.domain.entity.student_mark import StudentMarkEntity
from shared.domain.value.identifier import StudentID, TargetID


@dataclass(frozen=True)
class ScoreExportResult:
    """エクスポート結果"""
    backup_path: Path | None
    success: bool
    error_message: str | None


class IScoreExportUseCase(ABC):
    """点数エクスポートUseCaseのインターフェース"""

    @abstractmethod
    def list_worksheet_stats(
            self,
            *,
            excel_fullpath: Path,
            student_ids: list[StudentID],
    ) -> list[WorksheetStat]:
        """ワークシートの状態一覧を取得"""
        raise NotImplementedError()

    @abstractmethod
    def has_data(
            self,
            *,
            excel_fullpath: Path,
            worksheet_name: str,
            student_ids: list[StudentID],
            target_id: TargetID,
    ) -> bool:
        """指定された位置にデータが存在するか"""
        raise NotImplementedError()

    @abstractmethod
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
        raise NotImplementedError()
