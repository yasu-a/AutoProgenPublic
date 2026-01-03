from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from feature.export.domain.value import ExcelColumnMapping, ExcelRowRange
from shared.domain.value.identifier import TargetID, StudentID

if TYPE_CHECKING:
    from shared.domain.value.excel_cell_table import ExcelCellTable


class ExcelLayoutDetectionError(Exception):
    """Excelレイアウト検出で発生するエラーの基底クラス"""
    pass


class HeaderRowNotFoundError(ExcelLayoutDetectionError):
    """ヘッダー行（学籍番号列）が見つからないエラー"""
    pass


class StudentNameColumnNotFoundError(ExcelLayoutDetectionError):
    """氏名列が見つからないエラー"""
    pass


class ScoreColumnNotFoundError(ExcelLayoutDetectionError):
    """設問番号列が見つからないエラー"""

    def __init__(self, target_id: TargetID):
        self.target_id = target_id
        super().__init__()


class DataRowNotFoundError(ExcelLayoutDetectionError):
    """データ行が見つからないエラー"""
    pass


class ExcelScoreUpdatePlanningError(Exception):
    """Excel点数更新計画で発生するエラーの基底クラス"""
    pass


class StudentNameMismatchError(ExcelScoreUpdatePlanningError):
    """氏名が一致しないエラー"""

    def __init__(self, student_id: StudentID, row_index: int, excel_name: str, expected_name: str):
        self.student_id = student_id
        self.row_index = row_index
        self.excel_name = excel_name
        self.expected_name = expected_name
        super().__init__(
            f"行{row_index + 1}: 学籍番号 {student_id} の氏名が一致しません。"
            f"Excel: '{excel_name}', 期待値: '{expected_name}'"
        )


class InvalidStudentIdError(ExcelScoreUpdatePlanningError):
    """無効な学籍番号エラー"""

    def __init__(self, row_index: int, value: str):
        self.row_index = row_index
        self.value = value
        super().__init__(f"行{row_index + 1}: 無効な学籍番号 '{value}'")


class IExcelLayoutDetectionService(ABC):
    """Excelレイアウト検出サービス"""

    @abstractmethod
    def execute(
        self,
        *,
        excel_cell_table: "ExcelCellTable",
        target_id: TargetID,
    ) -> tuple[ExcelColumnMapping, ExcelRowRange]:
        """
        単純なヒューリスティックで列を特定する。
        - "# 学籍番号" または "学籍番号" がある行をヘッダーとする
        - その行にある "問X" をターゲット列とする

        Raises:
            HeaderRowNotFoundError: ヘッダー行（学籍番号列）が見つからない場合
            StudentNameColumnNotFoundError: 氏名列が見つからない場合
            ScoreColumnNotFoundError: 設問番号列が見つからない場合
            DataRowNotFoundError: データ行が見つからない場合
        """
        raise NotImplementedError()


@dataclass(frozen=True)
class StudentScoreDataDto:
    """学生の点数データDTO"""
    name: str
    score: int | None  # 未採点はNone


class IExcelScoreUpdatePlanningService(ABC):
    """Excel点数更新計画サービス"""

    @abstractmethod
    def execute(
        self,
        *,
        excel_cell_table: "ExcelCellTable",
        student_score_map: dict[StudentID, StudentScoreDataDto],
        column_mapping: ExcelColumnMapping,
        row_range: ExcelRowRange,
    ) -> dict[tuple[int, int], int | None]:
        """
        Excelの現状データと正解データを突き合わせ、更新内容を計算する

        Args:
            excel_cell_table: Excelセルテーブルデータ
            student_score_map: 学生ID -> 点数データのマッピング
            column_mapping: 列マッピング設定
            row_range: 行範囲設定

        Returns:
            更新対象セルのマッピング: (row_index, column_index) -> score (未採点はNone)

        Raises:
            StudentNameMismatchError: 氏名が一致しない場合
            InvalidStudentIdError: 無効な学籍番号の場合
        """
        raise NotImplementedError()
