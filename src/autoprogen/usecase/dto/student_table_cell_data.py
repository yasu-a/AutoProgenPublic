from dataclasses import dataclass
from enum import Enum, auto

from autoprogen.domain.error.stage.base import StageError
from autoprogen.domain.model.stage_path import StagePath
from autoprogen.domain.model.stage import AbstractStage
from autoprogen.domain.model.value import StudentID


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
    # 一覧と詳細画面へ表示する短い説明。
    summary_text: str
    # エラー固有情報を含む詳細な説明。
    detailed_text: str
    # 表示内容の生成元となった構造化ステージエラー。表示専用データではNoneを許容する。
    error: StageError | None = None


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
