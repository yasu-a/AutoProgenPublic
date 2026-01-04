from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Callable

from shared.domain.value.identifier import StudentID
from shared.domain.value.stage import AbstractStage
from shared.domain.value.stage_path import StagePath


# DTOはinterfaceの直上に定義
@dataclass
class ResourceUsageGetResultDto:
    """リソース使用状況取得UseCaseの結果を表すDTO"""
    disk_read_count: int
    disk_write_count: int
    cpu_percent: int
    memory_mega_bytes: int


@dataclass
class StudentStageResultDiffSnapshotDto:
    """学生動的データ差分スナップショット取得UseCaseの結果を表すDTO"""
    student_id: StudentID
    timestamp: datetime | None

    def is_modified_from(self, other):
        if not isinstance(other, StudentStageResultDiffSnapshotDto):
            return NotImplemented
        assert self.student_id == other.student_id, (self.student_id, other.student_id)
        return self.timestamp != other.timestamp


@dataclass
class StudentIDCellDataDto:
    """学生テーブル学生IDセルデータ取得UseCaseの結果を表すDTO"""
    student_id: StudentID
    is_submission_folder_link_alive: bool  # 提出フォルダへのリンクが生きているかどうか（提出データが存在するかどうか）


@dataclass
class StudentNameCellDataDto:
    """学生テーブル学生名セルデータ取得UseCaseの結果を表すDTO"""
    student_id: StudentID
    student_name: str


class StudentStageStateCellDataStageState(Enum):
    """学生ステージ状態セルデータの状態を表すEnum"""
    UNFINISHED = auto()
    FINISHED_SUCCESS = auto()
    FINISHED_FAILURE = auto()


@dataclass
class StudentStageStateCellDataDto:
    """学生テーブル学生ステージ状態セルデータ取得UseCaseの結果を表すDTO"""
    student_id: StudentID
    stage_type: type[AbstractStage]
    states: dict[StagePath, StudentStageStateCellDataStageState]


@dataclass(frozen=True)
class StudentErrorCellDataTextEntryDto:
    """学生エラーセルデータのテキストエントリを表すDTO"""
    summary_text: str
    detailed_text: str


@dataclass
class StudentErrorCellDataDto:
    """学生テーブル学生エラーセルデータ取得UseCaseの結果を表すDTO"""
    student_id: StudentID
    text_entries: list[StudentErrorCellDataTextEntryDto]

    def aggregate_text_entries(self) -> list[StudentErrorCellDataTextEntryDto]:
        seen = set()
        aggregated_text_entries = []
        for text_entry in self.text_entries:
            if text_entry.summary_text not in seen:
                aggregated_text_entries.append(text_entry)
                seen.add(text_entry.summary_text)
        return aggregated_text_entries


class IStudentListIDUseCase(ABC):
    """学生ID一覧取得UseCaseのインターフェース"""

    @abstractmethod
    def execute(self) -> list[StudentID]:
        raise NotImplementedError()


class IResourceUsageGetUseCase(ABC):
    """リソース使用状況取得UseCaseのインターフェース"""

    @abstractmethod
    def execute(self) -> ResourceUsageGetResultDto:
        raise NotImplementedError()


class IStudentStageResultClearUseCase(ABC):
    """学生ステージ結果クリアUseCaseのインターフェース"""

    @abstractmethod
    def execute(
            self,
            *,
            student_id: StudentID,
            stop_producer: Callable[[], bool],  # 停止するときTrueを受け取る
    ) -> None:
        raise NotImplementedError()


class IStudentDynamicTakeDiffSnapshotUseCase(ABC):
    """学生動的データ差分スナップショット取得UseCaseのインターフェース"""

    @abstractmethod
    def execute(self, student_id: StudentID) -> StudentStageResultDiffSnapshotDto:
        raise NotImplementedError()


class IStudentSubmissionFolderShowUseCase(ABC):
    """学生提出フォルダ表示UseCaseのインターフェース"""

    @abstractmethod
    def execute(self, student_id: StudentID) -> None:
        raise NotImplementedError()


class IStudentTableGetStudentIDCellDataUseCase(ABC):
    """学生テーブル学生IDセルデータ取得UseCaseのインターフェース"""

    @abstractmethod
    def execute(self, student_id: StudentID) -> StudentIDCellDataDto:
        raise NotImplementedError()


class IStudentTableGetStudentNameCellDataUseCase(ABC):
    """学生テーブル学生名セルデータ取得UseCaseのインターフェース"""

    @abstractmethod
    def execute(self, student_id: StudentID) -> StudentNameCellDataDto:
        raise NotImplementedError()


class IStudentTableGetStudentStageStateCellDataUseCase(ABC):
    """学生テーブル学生ステージ状態セルデータ取得UseCaseのインターフェース"""

    @abstractmethod
    def execute(self, student_id: StudentID, stage_type: type[AbstractStage]) -> StudentStageStateCellDataDto:
        raise NotImplementedError()


class IStudentTableGetStudentErrorCellDataUseCase(ABC):
    """学生テーブル学生エラーセルデータ取得UseCaseのインターフェース"""

    @abstractmethod
    def execute(self, student_id: StudentID) -> StudentErrorCellDataDto:
        raise NotImplementedError()


class IStudentRunBuildStageUseCase(ABC):
    """学生ビルドステージ実行UseCaseのインターフェース"""

    @abstractmethod
    def execute(self, student_id: StudentID, stage_path: StagePath) -> None:
        raise NotImplementedError()


class IStudentRunCompileStageUseCase(ABC):
    """学生コンパイルステージ実行UseCaseのインターフェース"""

    @abstractmethod
    def execute(self, student_id: StudentID, stage_path: StagePath) -> None:
        raise NotImplementedError()


class IStudentRunExecuteStageUseCase(ABC):
    """学生実行ステージ実行UseCaseのインターフェース"""

    @abstractmethod
    def execute(self, student_id: StudentID, stage_path: StagePath) -> None:
        raise NotImplementedError()


class IStudentRunTestStageUseCase(ABC):
    """学生テストステージ実行UseCaseのインターフェース"""

    @abstractmethod
    def execute(self, student_id: StudentID, stage_path: StagePath) -> None:
        raise NotImplementedError()


class IStudentRunNextStageUseCase(ABC):
    """学生次のステージ実行UseCaseのインターフェース"""

    @abstractmethod
    def execute(
            self,
            *,
            student_id: StudentID,
            stop_producer: Callable[[], bool],  # 停止するときTrueを受け取る
    ) -> None:
        raise NotImplementedError()
