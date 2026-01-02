from pathlib import Path

from feature.export.usecase.interface import IExecuteSimpleScoreExportUseCase
from feature.export.domain.interface.gateway import ISimpleScoreExportGateway
from feature.export.domain.model.data import SimpleScoreExportRow
from feature.export.domain.model.format import ScoreExportFormat


class ExecuteSimpleScoreExportUseCase(IExecuteSimpleScoreExportUseCase):
    def __init__(
        self,
        *,
        json_export_gateway: ISimpleScoreExportGateway,
        csv_export_gateway: ISimpleScoreExportGateway,
    ):
        self._json_export_gateway = json_export_gateway
        self._csv_export_gateway = csv_export_gateway
    
    def execute(
        self,
        *,
        folder: Path,
        filename_no_ext: str,
        format: ScoreExportFormat,
        data: list[SimpleScoreExportRow],
    ) -> Path:
        """単純エクスポートを実行"""
        ext = ".csv" if format == ScoreExportFormat.CSV else ".json"
        fullpath = folder / (filename_no_ext + ext)
        
        if format == ScoreExportFormat.CSV:
            self._csv_export_gateway.save(fullpath, data)
        else:
            self._json_export_gateway.save(fullpath, data)
            
        return fullpath

