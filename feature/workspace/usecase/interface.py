from abc import ABC, abstractmethod
from typing import Callable

from feature.workspace.usecase.dto import (
    ResourceUsageGetResult,
    StudentStageResultDiffSnapshot,
    StudentIDCellData,
    StudentNameCellData,
    StudentStageStateCellData,
    StudentErrorCellData,
)
from shared.domain.entity.student_stage_path_result import StudentStagePathResultEntity
from shared.domain.value.identifier import StudentID
from shared.domain.value.stage import AbstractStage
from shared.domain.value.stage_path import StagePath


class IStudentListIDUseCase(ABC):
    """学生ID一覧取得UseCaseのインターフェース"""

    @abstractmethod
    def execute(self) -> list[StudentID]:
        raise NotImplementedError()


class IResourceUsageGetUseCase(ABC):
    """リソース使用状況取得UseCaseのインターフェース"""

    @abstractmethod
    def execute(self) -> ResourceUsageGetResult:
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
    def execute(self, student_id: StudentID) -> StudentStageResultDiffSnapshot:
        raise NotImplementedError()


class IStudentSubmissionFolderShowUseCase(ABC):
    """学生提出フォルダ表示UseCaseのインターフェース"""

    @abstractmethod
    def execute(self, student_id: StudentID) -> None:
        raise NotImplementedError()


class IStudentTableGetStudentIDCellDataUseCase(ABC):
    """学生テーブル学生IDセルデータ取得UseCaseのインターフェース"""

    @abstractmethod
    def execute(self, student_id: StudentID) -> StudentIDCellData:
        raise NotImplementedError()


class IStudentTableGetStudentNameCellDataUseCase(ABC):
    """学生テーブル学生名セルデータ取得UseCaseのインターフェース"""

    @abstractmethod
    def execute(self, student_id: StudentID) -> StudentNameCellData:
        raise NotImplementedError()


class IStudentTableGetStudentStageStateCellDataUseCase(ABC):
    """学生テーブル学生ステージ状態セルデータ取得UseCaseのインターフェース"""

    @abstractmethod
    def execute(self, student_id: StudentID, stage_type: type[AbstractStage]) -> StudentStageStateCellData:
        raise NotImplementedError()


class IStudentTableGetStudentErrorCellDataUseCase(ABC):
    """学生テーブル学生エラーセルデータ取得UseCaseのインターフェース"""

    @abstractmethod
    def execute(self, student_id: StudentID) -> StudentErrorCellData:
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
