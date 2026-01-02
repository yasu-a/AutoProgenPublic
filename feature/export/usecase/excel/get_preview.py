from pathlib import Path

from feature.export.usecase.interface import (
    IListExcelWorksheetUseCase,
    IGetExcelSheetPreviewUseCase,
)
from shared.domain.interface.gateway import IExcelGateway


class ListExcelWorksheetUseCase(IListExcelWorksheetUseCase):
    def __init__(self, *, excel_gateway: IExcelGateway):
        self._excel_gateway = excel_gateway
    
    def execute(self, *, excel_path: Path) -> list[str]:
        """Excelワークシート名の一覧を取得"""
        return self._excel_gateway.list_sheet_names(excel_path)


class GetExcelSheetPreviewUseCase(IGetExcelSheetPreviewUseCase):
    def __init__(self, *, excel_gateway: IExcelGateway):
        self._excel_gateway = excel_gateway
    
    def execute(
        self,
        *,
        excel_path: Path,
        sheet_name: str,
    ) -> dict[tuple[int, int], str]:
        """Excelシートのプレビュー（範囲制限あり）を取得"""
        excel_cell_table = self._excel_gateway.get_sheet_cells(
            excel_path,
            sheet_name,
            max_rows=300,
            max_cols=20,
        )
        return excel_cell_table.get_data()

