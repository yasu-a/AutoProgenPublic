from dataclasses import dataclass

from shared.domain.value.identifier import StudentID


# 全てのイベントの親
class DomainEvent:
    pass


@dataclass(frozen=True)
class StudentUpdateEvent(DomainEvent):
    """学生データが更新されたことを示すイベント"""
    student_id: StudentID
