from dataclasses import dataclass


@dataclass(frozen=True)
class ExcelColumnMapping:
    """Excelの列インデックス（0-based）を保持する設定値"""
    student_id_column_index: int
    student_name_column_index: int  # 氏名列
    score_write_column_index: int  # 書き込み対象の列


@dataclass(frozen=True)
class ExcelRowRange:
    """処理対象の行範囲（0-based）"""
    start_row_index: int
    end_row_index: int  # 学籍番号で埋まっている最後の行（0-based）
