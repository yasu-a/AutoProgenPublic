import json
from pathlib import Path

from feature.export.domain.interface.gateway import (
    ISimpleScoreExportGateway,
    SimpleScoreExportGatewayError,
)
from feature.export.domain.model.data import SimpleScoreExportRow


class JsonScoreExportGateway(ISimpleScoreExportGateway):
    """JSONエクスポートGatewayの実装"""
    
    def save(self, path: Path, data: list[SimpleScoreExportRow]) -> None:
        """
        JSON形式でデータを保存
        
        Args:
            path: 保存先のパス（拡張子は含まれている想定）
            data: エクスポートするデータ
        """
        try:
            # データを辞書のリストに変換
            dicts = [
                {
                    "student_id": str(r.student_id),
                    "name": r.student_name,
                    "score": r.score
                }
                for r in data
            ]
            with open(path, mode="w", encoding="utf-8") as f:
                json.dump(dicts, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise SimpleScoreExportGatewayError(f"JSON保存に失敗しました: {e}") from e

