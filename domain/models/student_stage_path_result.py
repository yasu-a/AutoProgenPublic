from collections import OrderedDict
from enum import Enum
from typing import Iterable

from domain.models.stage_path import StagePath
from domain.models.stages import AbstractStage
from domain.models.student_stage_result import AbstractStudentStageResult, \
    AbstractFailureStudentStageResult
from domain.models.values import StudentID


class StudentStagePathResult:
    # ステージとその結果を管理するクラス
    # "last_stage"とは最後に処理されたステージであり、ステージパスの最後のステージではない

    def __init__(
            self,
            *,
            student_id: StudentID,
            stage_results: OrderedDict[AbstractStage, AbstractStudentStageResult | None],
            # ^ None if unprocessed
    ):
        if len(stage_results) == 0:
            raise ValueError("stage_results must not be empty")

        for stage_result in stage_results.values():
            if stage_result is None:
                continue
            if stage_result.student_id != student_id:
                raise ValueError(
                    f"student_id mismatch: "
                    f"stage_result.student_id={stage_result.student_id} "
                    f"!= self.student_id={student_id}"
                )

        self._student_id = student_id
        self._stage_results = stage_results

    @property
    def student_id(self) -> StudentID:
        return self._student_id

    def iter_stage_results(self) \
            -> Iterable[tuple[AbstractStage, AbstractStudentStageResult | None]]:
        return iter(self._stage_results.items())

    @property
    def stage_path(self) -> StagePath:
        # ステージのパスを取得する
        return StagePath(self._stage_results.keys())

    def _check_stage_exists(self, stage: AbstractStage):
        if stage not in self._stage_results:
            raise ValueError(f"stage not included in this path: {stage}")

    def get_result(self, stage: AbstractStage) -> AbstractStudentStageResult | None:
        self._check_stage_exists(stage)
        return self._stage_results[stage]

    def has_result(self, stage: AbstractStage) -> bool:
        self._check_stage_exists(stage)
        return self._stage_results[stage] is not None

    def put_result(self, result: AbstractStudentStageResult) -> None:
        self._check_stage_exists(result.stage)
        prev_stage = self.stage_path.get_previous_stage_of(result.stage)
        if prev_stage is not None and not self.has_result(prev_stage):
            raise ValueError(
                f"cannot set result: "
                f"previous stage of {result.stage} is not finished"
            )
        if result.student_id != self._student_id:
            raise ValueError(
                f"student_id mismatch: "
                f"result.student_id={result.student_id} "
                f"!= self.student_id={self._student_id}"
            )
        self._stage_results[result.stage] = result

    def delete_result(self, stage: AbstractStage):
        self._check_stage_exists(stage)
        next_stage = self.stage_path.get_next_stage_of(stage)
        if next_stage is not None and self.has_result(next_stage):
            raise ValueError(
                f"cannot delete result: "
                f"next stage of {stage} is not finished"
            )
        self._stage_results[stage] = None

    def delete_all_results(self) -> None:
        for stage in reversed(self.stage_path):
            self.delete_result(stage)

    class StageStatus(Enum):
        UNFINISHED = "unfinished"
        SUCCESS = "success"
        FAILURE = "failure"

    @property
    def stage_statuses(self) -> OrderedDict[AbstractStage, StageStatus]:
        # 各ステージに対して，結果が存在しないなら"unfinished"，成功なら"success"，失敗なら"failure"のマッピングを返す
        result_states = OrderedDict()
        for stage, stage_result in self._stage_results.items():
            if stage_result is None:
                result_states[stage] = self.StageStatus.UNFINISHED
            else:
                if stage_result.is_success:
                    result_states[stage] = self.StageStatus.SUCCESS
                else:
                    result_states[stage] = self.StageStatus.FAILURE
        return result_states

    def get_result_by_stage_type(self, stage_type: type[AbstractStage]) \
            -> AbstractStudentStageResult | None:  # None if unfinished or stage does not exist
        # TODO: 廃止 get_resultを使え
        # 指定されたステージタイプのステージの結果を取得する．未処理またはステージが存在しない場合はNoneを返す
        for stage in self._stage_results:
            if isinstance(stage, stage_type):
                return self._stage_results[stage]
        return None

    @property
    def _last_stage(self) -> AbstractStage | None:  # None if unstarted
        # 最後に処理されたステージを取得する．まだ開始されていない場合はNoneを返す
        latest_stage = None
        for stage, stage_result in self._stage_results.items():
            if stage_result is None:
                return latest_stage
            latest_stage = stage
        return latest_stage

    @property
    def _last_stage_result(self) -> AbstractStudentStageResult | None:  # None if unstarted
        # 最新の結果を取得する．まだ開始されていない場合はNoneを返す
        if self._last_stage is None:
            return None
        return self._stage_results[self._last_stage]

    @property
    def are_all_finished(self) -> bool:
        # すべてのステージが完了したかどうかを返す
        return self.get_next_stage() is None

    @property
    def is_last_stage_success(self) -> bool | None:  # None if unstarted
        # 成功したかどうかを返す．まだ開始されていない場合はNoneを返す
        last_result = self._last_stage_result
        if last_result is None:
            return None
        return last_result.is_success

    def get_next_stage(self) -> AbstractStage | None:
        # 結果がない場合は最初のステージ，すべて終了した場合はNone，
        # 最後に実行したステージが失敗している場合は同じステージ，成功している場合は次のステージを返す
        is_last_stage_success: bool | None = self.is_last_stage_success
        # 結果がないなら最初のステージを返す
        if is_last_stage_success is None:
            return self.stage_path.first_stage
        # 最後に実行したステージが失敗しているなら最後に実行したステージを返す
        if not is_last_stage_success:
            return self._last_stage
        # 次のステージを返す（次がなければNone）
        return self.stage_path.get_next_stage_of(self._last_stage)

    @property
    def last_stage_main_reason(self) -> str | None:  # None if unstarted or no error occurred
        # 主な理由を取得する．まだ開始されていない場合，またはエラーが発生していない場合はNoneを返す
        last_result = self._last_stage_result
        if last_result is None:
            return None
        if last_result.is_success:
            return None
        assert isinstance(last_result, AbstractFailureStudentStageResult)
        return last_result.reason

    @property
    def last_stage_detailed_reason(self) -> str | None:  # None if unstarted or no error occurred
        # 詳細な理由を取得する．まだ開始されていない場合，またはエラーが発生していない場合はNoneを返す
        last_result = self._last_stage_result
        if last_result is None:
            return None
        if last_result.is_success:
            return None
        assert isinstance(last_result, AbstractFailureStudentStageResult)
        return last_result.detailed_text

    def __repr__(self) -> str:
        # オブジェクトの文字列表現を返す
        return (
            f"{type(self).__name__}("
            f"success={self.is_last_stage_success}, "
            f"reason={self.last_stage_main_reason}"
            f")"
        )
