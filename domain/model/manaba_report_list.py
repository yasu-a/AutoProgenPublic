from pathlib import PurePosixPath
from typing import NamedTuple

from domain.model.value import StudentID


class ManabaReportListRow(NamedTuple):
    # 学籍番号（ドメイン値オブジェクト）。
    student_id: StudentID
    # 氏名（日本語）。
    name: str
    # 氏名（英語）。
    name_en: str
    # メールアドレス。
    email_address: str
    # 提出済みかどうか。
    is_submitted: bool
    # 提出日時の生文字列（パースは別責務）。
    submitted_at_text: str
    # 提出回数の生文字列（数値化は別責務）。
    num_submissions_text: str
    # 提出フォルダ相対パス。未提出時は None。
    submission_folder_path: PurePosixPath | None


class ManabaReportList:
    # 履修生行のみを保持した不変コレクション。
    _rows: tuple[ManabaReportListRow, ...]

    def __init__(self, *, rows: tuple[ManabaReportListRow, ...]) -> None:
        # Parser が検証済みの行集合を受け取って保持する。
        self._rows = rows

    def row_count(self) -> int:
        # 履修生行の件数を返す。
        return len(self._rows)

    def get_row(self, *, row_index: int) -> ManabaReportListRow:
        # 指定インデックスの履修生行を返す。
        return self._rows[row_index]
