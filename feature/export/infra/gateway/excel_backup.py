import shutil
from datetime import datetime
from pathlib import Path

from feature.export.domain.interface.gateway import (
    IExcelBackupGateway,
    ExcelBackupGatewayError,
)


class ExcelBackupGateway(IExcelBackupGateway):
    """ExcelバックアップGatewayの実装"""
    
    def create_backup(self, excel_path: Path) -> Path:
        """
        Excelファイルのバックアップを作成
        
        Args:
            excel_path: バックアップ元のExcelファイルのパス
        
        Returns:
            バックアップファイルのパス
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = excel_path.parent / f"{excel_path.stem}_backup_{timestamp}.xlsx"
            # 既存ファイルをコピーしてバックアップとする
            shutil.copy2(excel_path, backup_path)
            return backup_path
        except Exception as e:
            raise ExcelBackupGatewayError(f"バックアップの作成に失敗しました: {e}") from e

