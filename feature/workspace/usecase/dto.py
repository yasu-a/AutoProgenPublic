from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto

from shared.domain.value.identifier import StudentID
from shared.domain.value.stage import AbstractStage
from shared.domain.value.stage_path import StagePath


@dataclass
class ResourceUsageGetResult:
    disk_read_count: int
    disk_write_count: int
    cpu_percent: int
    memory_mega_bytes: int


@dataclass
class StudentStageResultDiffSnapshot:
    student_id: StudentID
    timestamp: datetime | None

    def is_modified_from(self, other):
        if not isinstance(other, StudentStageResultDiffSnapshot):
            return NotImplemented
        assert self.student_id == other.student_id, (self.student_id, other.student_id)
        return self.timestamp != other.timestamp


@dataclass
class StudentIDCellData:
    # 生徒IDを表示して提出フォルダへのリンクを貼る機能を実現するために必要なデータ
    student_id: StudentID
    student_number: str  # 学籍番号の文字列
    is_submission_folder_link_alive: bool  # 提出フォルダへのリンクが生きているかどうか（提出データが存在するかどうか）


@dataclass
class StudentNameCellData:
    student_id: StudentID
    student_name: str


class StudentStageStateCellDataStageState(Enum):
    UNFINISHED = auto()
    FINISHED_SUCCESS = auto()
    FINISHED_FAILURE = auto()


@dataclass
class StudentStageStateCellData:
    student_id: StudentID
    stage_type: type[AbstractStage]
    states: dict[StagePath, StudentStageStateCellDataStageState]


@dataclass(frozen=True)
class StudentErrorCellDataTextEntry:
    summary_text: str
    detailed_text: str


@dataclass
class StudentErrorCellData:
    student_id: StudentID
    text_entries: list[StudentErrorCellDataTextEntry]

    def aggregate_text_entries(self) -> list[StudentErrorCellDataTextEntry]:
        seen = set()
        aggregated_text_entries = []
        for text_entry in self.text_entries:
            if text_entry.summary_text not in seen:
                aggregated_text_entries.append(text_entry)
                seen.add(text_entry.summary_text)
        return aggregated_text_entries
