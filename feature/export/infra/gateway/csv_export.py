import csv
from pathlib import Path

from feature.export.domain.interface.gateway import (
    ISimpleScoreExportGateway,
    SimpleScoreExportGatewayError,
)
from feature.export.usecase.interface import SimpleScoreExportRowDto


class CsvScoreExportGateway(ISimpleScoreExportGateway):
    """CSVエクスポートGatewayの実装"""
    
    def save(self, path: Path, data: list[SimpleScoreExportRowDto]) -> None:
        """
        CSV形式でデータを保存
        
        Args:
            path: 保存先のパス（拡張子は含まれている想定）
            data: エクスポートするデータ
        """
        try:
            # Excelでの利用を想定して utf-8-sig (BOM付き) にする
            with open(path, mode="w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["学籍番号", "氏名", "点数"])
                for row in data:
                    score_str = str(row.score) if row.score is not None else ""
                    writer.writerow([str(row.student_id), row.student_name, score_str])
        except Exception as e:
            raise SimpleScoreExportGatewayError(f"CSV保存に失敗しました: {e}") from e

