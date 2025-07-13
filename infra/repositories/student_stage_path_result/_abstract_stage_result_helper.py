from abc import ABC, abstractmethod

from domain.models.stages import AbstractStage
from domain.models.student_stage_result import AbstractStudentStageResult
from domain.models.values import StudentID


class _AbstractStageResultHelper(ABC):
    """ステージ結果処理の基底ヘルパークラス"""

    @abstractmethod
    def create_table_if_not_exists(self, cursor) -> None:
        """テーブルが存在しない場合に作成"""
        raise NotImplementedError()

    @abstractmethod
    def get_stage_result(self, cursor, student_id: StudentID,
                         stage: AbstractStage) -> AbstractStudentStageResult | None:
        """ステージ結果を取得"""
        raise NotImplementedError()

    @abstractmethod
    def put_stage_result(self, cursor, result: AbstractStudentStageResult) -> None:
        """ステージ結果を保存"""
        raise NotImplementedError()

    @abstractmethod
    def delete_stage_result(self, cursor, student_id: StudentID, stage: AbstractStage) -> None:
        """ステージ結果を削除"""
        raise NotImplementedError()

    @abstractmethod
    def exists_stage_result(self, cursor, student_id: StudentID, stage: AbstractStage) -> bool:
        """ステージ結果の存在チェック"""
        raise NotImplementedError()
