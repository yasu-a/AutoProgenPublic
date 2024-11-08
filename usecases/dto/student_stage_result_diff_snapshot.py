from dataclasses import dataclass
from datetime import datetime

from domain.models.values import StudentID


@dataclass
class StudentStageResultDiffSnapshot:
    student_id: StudentID
    timestamp: datetime | None


@dataclass
class StudentStageResultDiff:
    updated: bool

    @classmethod
    def from_snapshots(
            cls,
            *,
            old_snapshot: StudentStageResultDiffSnapshot,
            new_snapshot: StudentStageResultDiffSnapshot,
    ) -> "StudentStageResultDiff":
        return cls(
            updated=old_snapshot.timestamp != new_snapshot.timestamp,
        )
