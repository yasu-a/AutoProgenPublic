from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from feature.export.domain.model.data import SimpleScoreExportRow
from feature.export.domain.model.excel_layout import ExcelColumnMapping, ExcelRowRange
from feature.export.domain.model.format import ScoreExportFormat
from shared.domain.value.identifier import TargetID

if TYPE_CHECKING:
    from shared.domain.value.excel_cell_table import ExcelCellTable


@dataclass(frozen=True)
class ExportSettingDto:
    """エクスポート設定DTO"""
    backup_before_export: bool


# UseCaseインターフェース

class IGetSimpleScoreExportDataUseCase(ABC):
    """単純エクスポートデータ取得UseCase"""
    
    @abstractmethod
    def execute(self) -> list[SimpleScoreExportRow]:
        raise NotImplementedError()


class IExecuteSimpleScoreExportUseCase(ABC):
    """単純エクスポート実行UseCase"""
    
    @abstractmethod
    def execute(
        self,
        *,
        folder: Path,
        filename_no_ext: str,
        format: ScoreExportFormat,
        data: list[SimpleScoreExportRow],
    ) -> Path:
        raise NotImplementedError()


class IListExcelWorksheetUseCase(ABC):
    """Excelワークシート一覧取得UseCase"""
    
    @abstractmethod
    def execute(self, *, excel_path: Path) -> list[str]:
        raise NotImplementedError()


class IGetExcelSheetPreviewUseCase(ABC):
    """Excelシートプレビュー取得UseCase"""
    
    @abstractmethod
    def execute(
        self,
        *,
        excel_path: Path,
        sheet_name: str,
    ) -> dict[tuple[int, int], str]:
        """
        Args:
            excel_path: Excelファイルのパス
            sheet_name: シート名
        """
        raise NotImplementedError()


class IAutoDetectExcelLayoutUseCase(ABC):
    """Excelレイアウト自動検出UseCase"""
    
    @abstractmethod
    def execute(
        self,
        *,
        excel_cell_table: "ExcelCellTable",
        target_id: TargetID,
    ) -> tuple[ExcelColumnMapping, ExcelRowRange]:
        """
        Raises:
            ExcelLayoutDetectionError: レイアウト検出に失敗した場合
        """
        raise NotImplementedError()


class ExecuteExcelScoreUpdateError(Exception):
    """ExecuteExcelScoreUpdateUseCaseで発生するエラー"""
    pass


class IExecuteExcelScoreUpdateUseCase(ABC):
    """Excel点数更新実行UseCase"""
    
    @abstractmethod
    def execute(
        self,
        *,
        excel_path: Path,
        sheet_name: str,
        mapping: ExcelColumnMapping,
        row_range: ExcelRowRange,
    ) -> Path | None:
        """
        戻り値はバックアップパス
        
        Raises:
            ExecuteExcelScoreUpdateError: エクスポート処理でエラーが発生した場合
        """
        raise NotImplementedError()


class IExportSettingGetUseCase(ABC):
    """エクスポート設定取得UseCase"""
    
    @abstractmethod
    def execute(self) -> ExportSettingDto:
        raise NotImplementedError()
