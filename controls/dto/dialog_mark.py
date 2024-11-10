from dataclasses import dataclass

from domain.models.values import TestCaseID, StudentID, FileID


@dataclass
class MarkDialogState:
    # ダイアログの表示状態を表す

    student_id: StudentID | None = None  # 現在表示中の学籍番号 [^]
    testcase_id: TestCaseID | None = None  # 現在表示中のテストケースID [^]
    file_id: FileID | None = None  # 現在表示中のファイルID [^]
    # ^: Noneは未選択（表示がない状態）を表す
