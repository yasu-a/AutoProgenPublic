from abc import ABC
from dataclasses import dataclass

from domain.models.stages import AbstractStage
from domain.models.student_stage_result import AbstractStudentStageResult, \
    AbstractFailureStudentStageResult


@dataclass
class StudentStagePathResult(ABC):
    # ステージとその結果を管理するクラス
    stage_results: dict[AbstractStage, AbstractStudentStageResult | None]  # None if unprocessed

    def get_result_by_stage_type(self, stage_type: type[AbstractStage]) \
            -> AbstractStudentStageResult | None:  # None if unprocessed or stage does not exist
        for stage in self.stage_results:
            if isinstance(stage, stage_type):
                return self.stage_results[stage]
        return None

    def get_last_stage(self) -> AbstractStage | None:  # None if unstarted
        last_stage = None
        for stage, stage_result in self.stage_results.items():
            if stage_result is None:
                return last_stage
            last_stage = stage
        return last_stage

    def get_last_result(self) -> AbstractStudentStageResult | None:  # None if unstarted
        last_stage = self.get_last_stage()
        if last_stage is None:
            return None
        return self.stage_results[last_stage]

    def is_success(self) -> bool | None:  # None if unstarted
        last_result = self.get_last_result()
        if last_result is None:
            return None
        return last_result.is_success

    def get_main_reason(self) -> str | None:  # None if unstarted or no error occurred
        last_result = self.get_last_result()
        if last_result is None:
            return None
        if last_result.is_success:
            return None
        assert isinstance(last_result, AbstractFailureStudentStageResult)
        return last_result.reason

    def get_detailed_reason(self) -> str | None:  # None if unstarted or no error occurred
        last_result = self.get_last_result()
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
