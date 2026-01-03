from feature.export.domain.interface.service import IExcelLayoutDetectionService
from feature.export.domain.value import ExcelColumnMapping, ExcelRowRange
from feature.export.usecase.interface import IAutoDetectExcelLayoutUseCase
from shared.domain.value.excel_cell_table import ExcelCellTable
from shared.domain.value.identifier import TargetID


class AutoDetectExcelLayoutUseCase(IAutoDetectExcelLayoutUseCase):
    def __init__(
        self,
        *,
        excel_layout_detection_service: IExcelLayoutDetectionService,
    ):
        self._excel_layout_detection_service = excel_layout_detection_service
    
    def execute(
        self,
        *,
        excel_cell_table: ExcelCellTable,
        target_id: TargetID,
    ) -> tuple[ExcelColumnMapping, ExcelRowRange]:
        """Excelレイアウトを自動検出"""
        return self._excel_layout_detection_service.execute(
            excel_cell_table=excel_cell_table,
            target_id=target_id,
        )

