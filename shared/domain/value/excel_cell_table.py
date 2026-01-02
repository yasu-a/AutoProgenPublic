"""
ExcelセルテーブルのValue Object
"""
from typing import Any


class ExcelCellTable:
    """
    ExcelセルテーブルのValue Object
    
    フィールド:
        _data: セルデータ (row_index, column_index) -> cell_value のマッピング
            row_index, column_indexは0-based
    """
    
    def __init__(self, data: dict[tuple[int, int], str]):
        """
        初期化
        
        Args:
            data: セルデータのマッピング
        """
        if not isinstance(data, dict):
            raise TypeError(f"Expected 'data' to be dict, got {type(data).__name__}")
        
        self._data = dict(data)  # コピーを作成してimmutableにする
    
    def get_cell(self, row_index: int, column_index: int, default: str = "") -> str:
        """
        セルの値を取得
        
        Args:
            row_index: 行インデックス（0-based）
            column_index: 列インデックス（0-based）
            default: セルが存在しない場合のデフォルト値
        
        Returns:
            セルの値（存在しない場合はdefault）
        """
        return self._data.get((row_index, column_index), default)
    
    def get_data(self) -> dict[tuple[int, int], str]:
        """
        全セルデータを取得（コピーを返す）
        
        Returns:
            セルデータのマッピングのコピー
        """
        return dict(self._data)
    
    def is_empty(self) -> bool:
        """
        テーブルが空かどうかを判定
        
        Returns:
            空の場合はTrue
        """
        return len(self._data) == 0
    
    def get_rows(self) -> list[int]:
        """
        データが存在する行インデックスのリストを取得（ソート済み）
        
        Returns:
            行インデックスのリスト（0-based、ソート済み）
        """
        return sorted(list(set(r for r, c in self._data.keys())))
    
    def get_columns(self, row_index: int) -> list[int]:
        """
        指定された行にデータが存在する列インデックスのリストを取得（ソート済み）
        
        Args:
            row_index: 行インデックス（0-based）
        
        Returns:
            列インデックスのリスト（0-based、ソート済み）
        """
        return sorted([c for r, c in self._data.keys() if r == row_index])
    
    def __eq__(self, other: Any) -> bool:
        """値ベースの等価性判定"""
        if not isinstance(other, ExcelCellTable):
            return False
        return self._data == other._data
    
    def __hash__(self) -> int:
        """ハッシュ値（Value Objectとして辞書のキーに使えるように）"""
        return hash(tuple(sorted(self._data.items())))
    
    def __repr__(self) -> str:
        """文字列表現"""
        return f"ExcelCellTable(data_size={len(self._data)})"

