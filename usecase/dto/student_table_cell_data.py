from dataclasses import dataclass
from enum import Enum, auto

from domain.model.stage_path import StagePath
from domain.model.stage import AbstractStage
from domain.model.value import StudentID


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
