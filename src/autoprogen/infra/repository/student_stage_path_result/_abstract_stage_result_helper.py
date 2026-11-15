from abc import ABC, abstractmethod
import json

from autoprogen.domain.error.stage.base import StageError
from autoprogen.domain.model.stage import AbstractStage
from autoprogen.domain.model.student_stage_result import AbstractStudentStageResult
from autoprogen.domain.model.value import StudentID
from autoprogen.domain.service.stage_error_codec import StageErrorCodec, StageErrorRecord


class _AbstractStageResultHelper(ABC):
    """ステージ結果処理の基底ヘルパークラス"""

    _stage_error_codec = StageErrorCodec()

    def _encode_error(self, error: StageError) -> tuple[str, str, str]:
        """構造化エラーをSQLiteの三列へ保存できる値に変換する。"""
        record = self._stage_error_codec.encode(error)
        return (
            record.error_group_id,
            record.error_type_id,
            json.dumps(record.params, ensure_ascii=False, sort_keys=True),
        )

    def _decode_error(self, row) -> StageError | None:
        """SQLiteの三列を検証し、構造化エラーまたは成功を復元する。"""
        values = (
            row["error_group_id"],
            row["error_type_id"],
            row["error_params_json"],
        )
        if all(value is None for value in values):
            return None
        if any(value is None for value in values):
            raise ValueError("StageErrorの保存列が不完全です")
        try:
            params = json.loads(values[2])
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError("StageErrorのJSONが不正です") from exc
        return self._stage_error_codec.decode(StageErrorRecord(
            error_group_id=values[0],
            error_type_id=values[1],
            params=params,
        ))

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
