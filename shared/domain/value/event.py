from dataclasses import dataclass

from shared.domain.model.stage import Stage
from shared.domain.value.identifier import StudentID


# 全てのイベントの親
class DomainEvent:
    pass


@dataclass(frozen=True)
class StudentResultUpdateEvent(DomainEvent):
    """学生データが更新されたことを示すイベント"""
    student_id: StudentID


@dataclass(frozen=True)
class StudentProcessingStageUpdateEvent(DomainEvent):
    """学生の処理中のステージが更新されたことを示すイベント"""
    student_id: StudentID
    stage: Stage | None  # 処理中のステージがない

    def __post_init__(self):
        if self.stage is not None:
            assert self.stage in Stage, f"stage must be a Stage: {self.stage}"
