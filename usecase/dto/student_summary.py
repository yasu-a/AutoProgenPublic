from dataclasses import dataclass

from domain.model.value import StudentID


@dataclass
class StudentSummary:
    student_id: StudentID
    number: str
    name: str
