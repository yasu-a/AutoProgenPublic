from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypeVar, Generic

from domain.models.stages import StudentProgressStage
from domain.models.student_stage_result import AbstractStudentStageResult

_ResultType = TypeVar("_ResultType", bound=AbstractStudentStageResult)


@dataclass
class AbstractStudentProgress(ABC):
    # ステージとその結果を管理するクラス

    @abstractmethod
    def get_expected_next_stage(
            self) -> StudentProgressStage | None:  # None if all stages finished
        raise NotImplementedError()

    @abstractmethod
    def get_finished_stage(self) -> StudentProgressStage | None:  # None if no stages finished
        raise NotImplementedError()

    @abstractmethod
    def is_success(self) -> bool | None:  # None if no stages finished
        raise NotImplementedError()

    @abstractmethod
    def get_main_reason(self) -> str | None:  # None if no stages finished or no error occurred
        raise NotImplementedError()

    @abstractmethod
    def get_detailed_reason(self) -> str | None:
        raise NotImplementedError()

    def __repr__(self) -> str:
        return (f"{type(self).__name__}("
                f"success={self.is_success()}, "
                f"reason={self.get_main_reason()}, "
                f"next_stage={self.get_expected_next_stage()!r}"
                f")")


class StudentProgressWithFinishedStage(AbstractStudentProgress, Generic[_ResultType]):
    def __init__(self, *, stage: StudentProgressStage, result: _ResultType):
        self._stage = stage
        self._result = result

    def get_expected_next_stage(self) -> StudentProgressStage | None:
        if self._result.is_success():
            return self._stage.get_next_stage()
        else:
            return self._stage

    def get_finished_stage(self) -> StudentProgressStage | None:
        return self._stage

    def is_success(self) -> bool | None:
        return self._result.is_success()

    def get_main_reason(self) -> str | None:
        return self._result.reason

    def get_detailed_reason(self) -> str | None:
        return self._result.detailed_reason

    def get_result(self) -> _ResultType:
        return self._result


class StudentProgressUnstarted(AbstractStudentProgress):
    def get_expected_next_stage(self) -> StudentProgressStage | None:
        return StudentProgressStage.get_first_stage()

    def get_finished_stage(self) -> StudentProgressStage | None:
        return None

    def is_success(self) -> bool | None:
        return None

    def get_main_reason(self) -> str | None:
        return None

    def get_detailed_reason(self) -> str | None:
        return None
