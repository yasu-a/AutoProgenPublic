from dataclasses import dataclass

from domain.models.values import TestCaseID, StudentID, FileID


@dataclass
class MarkDialogState:
    student_id: StudentID | None = None
    testcase_id: TestCaseID | None = None
    file_id: FileID | None = None
