from dataclasses import dataclass
from datetime import datetime

from domain.models.values import StudentID


@dataclass
class StudentStageResultDiffSnapshot:
    student_id: StudentID
    timestamp: datetime | None

    def is_different_from(self, other):
        if not isinstance(other, StudentStageResultDiffSnapshot):
            return NotImplemented
        return self.timestamp == other.timestamp
