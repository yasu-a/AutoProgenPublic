from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from shared.domain.value.identifier import StudentID

if TYPE_CHECKING:
    from shared.domain.value.excel_cell_table import ExcelCellTable


class ICurrentDatetimeGateway(ABC):
    @abstractmethod
    def execute(self) -> datetime:
        raise NotImplementedError()


class IStudentSubmissionGetSourceContentGateway(ABC):
    @abstractmethod
    def execute(self, student_id: StudentID) -> str:
        raise NotImplementedError()


class IStudentSubmissionGetChecksumGateway(ABC):
    @abstractmethod
    def execute(self, student_id: StudentID) -> int:
        raise NotImplementedError()


class IStudentSubmissionFolderShowGateway(ABC):
    @abstractmethod
    def execute(self, student_id: StudentID) -> None:
        raise NotImplementedError()


class ExcelGatewayError(Exception):
    """ExcelGatewayで発生するエラー"""
    pass


class IExcelGateway(ABC):
    """Excel読み書き用のGateway"""
    
    @abstractmethod
    def list_sheet_names(self, excel_path: Path) -> list[str]:
        """シート名の一覧を取得"""
        raise NotImplementedError()
    
    @abstractmethod
    def get_sheet_cells(
        self,
        excel_path: Path,
        sheet_name: str,
        *,
        max_rows: int | None = None,
        max_cols: int | None = None,
    ) -> "ExcelCellTable":
        """
        シートのセルを取得
        
        Args:
            excel_path: Excelファイルのパス
            sheet_name: シート名
            max_rows: 読み込む最大行数（Noneの場合は全行）
            max_cols: 読み込む最大列数（Noneの場合は全列）
        
        Returns:
            ExcelCellTable: ExcelセルテーブルのValue Object
        """
        raise NotImplementedError()
    
    @abstractmethod
    def update_sheet_cells(
        self,
        *,
        excel_path: Path,
        sheet_name: str,
        values: dict[tuple[int, int], Any],
    ) -> None:
        """
        シートのセルを更新
        
        Args:
            excel_path: Excelファイルのパス
            sheet_name: シート名
            values: (row_index, column_index) -> value のマッピング
                row_index, column_indexは0-based
        """
        raise NotImplementedError()
