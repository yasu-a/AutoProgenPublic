from dataclasses import dataclass
from datetime import datetime

from domain.model.value import StudentID


@dataclass
class StudentStageResultDiffSnapshot:
    student_id: StudentID
    timestamp: datetime | None

    def is_modified_from(self, other):
        if not isinstance(other, StudentStageResultDiffSnapshot):
            return NotImplemented
        assert self.student_id == other.student_id, (self.student_id, other.student_id)
        return self.timestamp != other.timestamp
