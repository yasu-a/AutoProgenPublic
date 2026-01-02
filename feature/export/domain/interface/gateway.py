from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from feature.export.domain.model.data import SimpleScoreExportRow
from feature.export.domain.model.excel_layout import ExcelColumnMapping, ExcelRowRange
from shared.domain.value.identifier import StudentID


class SimpleScoreExportGatewayError(Exception):
    """SimpleScoreExportGatewayで発生するエラー"""
    pass


class ISimpleScoreExportGateway(ABC):
    """単純エクスポート（CSV/JSON）用のGatewayインターフェース"""

    @abstractmethod
    def save(self, path: Path, data: list[SimpleScoreExportRow]) -> None:
        """データを保存"""
        raise NotImplementedError()


class ExcelBackupGatewayError(Exception):
    """ExcelBackupGatewayで発生するエラー"""
    pass


class IExcelBackupGateway(ABC):
    """Excelバックアップ用のGateway"""

    @abstractmethod
    def create_backup(self, excel_path: Path) -> Path:
        """
        Excelファイルのバックアップを作成

        Returns:
            バックアップファイルのパス
        """
        raise NotImplementedError()
