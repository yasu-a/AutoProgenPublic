from dataclasses import dataclass

from domain.models.values import StudentID


@dataclass
class StudentSummary:
    student_id: StudentID
    number: str
    name: str
