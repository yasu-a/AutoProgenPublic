from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from shared.domain.entity.student_mark import StudentMarkEntity
from shared.domain.value.identifier import StudentID, TargetID


@dataclass(frozen=True)
class WorksheetStat:
    """ワークシートの状態"""
    name: str
    valid: bool
    message: str | None


class IScoreExcelIO(ABC):
    """Excelファイルへの点数エクスポートを行うIOのインターフェース"""

    @abstractmethod
    def list_worksheet_stats(
        self,
        *,
        student_ids: list[StudentID],
    ) -> list[WorksheetStat]:
        """ワークシートの状態一覧を取得"""
        raise NotImplementedError()

    @abstractmethod
    def has_data(
        self,
        *,
        worksheet_name: str,
        student_ids: list[StudentID],
        target_id: TargetID,
    ) -> bool:
        """指定された位置にデータが存在するか"""
        raise NotImplementedError()

    @abstractmethod
    def apply(
        self,
        *,
        worksheet_name: str,
        student_marks: list[StudentMarkEntity],
        target_id: TargetID,
        do_backup: bool,
    ) -> Path | None:
        """点数をエクスポート（バックアップパスを返す）"""
        raise NotImplementedError()

