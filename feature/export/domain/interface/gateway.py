from abc import ABC, abstractmethod
from pathlib import Path

from feature.export.usecase.interface import SimpleScoreExportRowDto


class SimpleScoreExportGatewayError(Exception):
    """SimpleScoreExportGatewayで発生するエラー"""
    pass


class ISimpleScoreExportGateway(ABC):
    """単純エクスポート（CSV/JSON）用のGatewayインターフェース"""

    @abstractmethod
    def save(self, path: Path, data: list[SimpleScoreExportRowDto]) -> None:
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
