from abc import ABC
from collections import OrderedDict
from dataclasses import dataclass

from domain.models.stage_path import StagePath
from domain.models.stages import AbstractStage
from domain.models.student_stage_result import AbstractStudentStageResult, \
    AbstractFailureStudentStageResult


@dataclass
class StudentStagePathResult(ABC):
    # ステージとその結果を管理するクラス
    stage_results: OrderedDict[AbstractStage, AbstractStudentStageResult | None]

    # stage_results: None if unprocessed

    def get_finish_states(self) -> OrderedDict[AbstractStage, bool | None]:
        # 各ステージに対して，結果が存在しないならNone，成功ならTrue，失敗ならFalseのマッピングを返す
        result_states = OrderedDict()
        for stage, stage_result in self.stage_results.items():
            if stage_result is None:
                result_states[stage] = None
            else:
                result_states[stage] = stage_result.is_success
        return result_states

    def get_result_by_stage_type(self, stage_type: type[AbstractStage]) \
            -> AbstractStudentStageResult | None:  # None if unprocessed or stage does not exist
        for stage in self.stage_results:
            if isinstance(stage, stage_type):
                return self.stage_results[stage]
        return None

    def get_latest_stage(self) -> AbstractStage | None:  # None if unstarted
        latest_stage = None
        for stage, stage_result in self.stage_results.items():
            if stage_result is None:
                return latest_stage
            latest_stage = stage
        return latest_stage

    def get_stage_path(self) -> StagePath:
        return StagePath(self.stage_results.keys())

    def get_next_stage(self) -> AbstractStage | None:
        # 結果がない場合は最初のステージ，すべて終了した場合はNone，
        # 最新のステージが失敗している場合は同じステージ，成功している場合は次のステージを返す
        stages = self.get_stage_path()
        latest_stage = self.get_latest_stage()
        if latest_stage is None:  # 結果がない
            return stages[0]
        if not self.stage_results[latest_stage].is_success:  # 最新のステージが失敗している
            return latest_stage
        latest_stage_index = stages.index(latest_stage)
        try:
            return stages[latest_stage_index + 1]
        except IndexError:
            return None

    def are_all_stages_done(self) -> bool:
        return self.get_next_stage() is None

    def get_latest_result(self) -> AbstractStudentStageResult | None:  # None if unstarted
        last_stage = self.get_latest_stage()
        if last_stage is None:
            return None
        return self.stage_results[last_stage]

    def is_success(self) -> bool | None:  # None if unstarted
        last_result = self.get_latest_result()
        if last_result is None:
            return None
        return last_result.is_success

    def get_main_reason(self) -> str | None:  # None if unstarted or no error occurred
        last_result = self.get_latest_result()
        if last_result is None:
            return None
        if last_result.is_success:
            return None
        assert isinstance(last_result, AbstractFailureStudentStageResult)
        return last_result.reason

    def get_detailed_reason(self) -> str | None:  # None if unstarted or no error occurred
        last_result = self.get_latest_result()
        if last_result is None:
            return None
        if last_result.is_success:
            return None
        assert isinstance(last_result, AbstractFailureStudentStageResult)
        return last_result.detailed_text

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f"success={self.is_success()}, "
            f"reason={self.get_main_reason()}, "
            f")"
        )
