from dataclasses import dataclass
from enum import Enum, auto

from domain.models.stage_path import StagePath
from domain.models.stages import AbstractStage
from domain.models.values import StudentID


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


@dataclass
class StudentErrorCellDataTextEntry:
    summary_text: str
    detailed_text: str


@dataclass
class StudentErrorCellData:
    student_id: StudentID
    text_entries: list[StudentErrorCellDataTextEntry]
