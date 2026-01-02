from dataclasses import dataclass

from shared.domain.value.identifier import StudentID


@dataclass(frozen=True)
class SimpleScoreExportRow:
    """単純エクスポート（JSON/CSV）用の1行分のデータ構造"""
    student_id: StudentID
    student_name: str
    score: int | None  # 未採点はNone


@dataclass(frozen=True)
class StudentScoreData:
    """学生の点数データ"""
    name: str
    score: int | None  # 未採点はNone
