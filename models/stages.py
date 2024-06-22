from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import IntEnum
from typing import TypeVar, Generic

from models.reuslts import AbstractResult


class StudentProgressStage(IntEnum):
    BUILD = 1
    COMPILE = 2
    EXECUTE = 3

    def get_next_stage(self) -> "StudentProgressStage | None":
        try:
            return StudentProgressStage(self.value + 1)
        except ValueError:
            return None

    @classmethod
    def get_first_stage(cls) -> "StudentProgressStage":
        return sorted(cls, key=lambda x: x.value)[0]

    # def __contains__(self, other) -> bool:
    #     if not isinstance(other, StudentProgressStage):
    #         return NotImplemented
    #     if self.value < other.value:
    #         return False
    #     return True


_ResultType = TypeVar("_ResultType", bound=AbstractResult)


@dataclass
class AbstractStudentProgress(ABC):
    @abstractmethod
    def get_expected_next_stage(
            self) -> StudentProgressStage | None:  # None means all stages finished
        raise NotImplementedError()

    @abstractmethod
    def get_finished_stage(self) -> StudentProgressStage | None:  # None means no stages finished
        raise NotImplementedError()

    @abstractmethod
    def is_success(self) -> bool | None:  # None means no stages finished
        raise NotImplementedError()

    @abstractmethod
    def get_main_reason(self) -> bool | None:  # None means no stages finished or no error occurred
        raise NotImplementedError()

    @abstractmethod
    def get_detailed_reason(self) -> bool | None:
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

    def get_main_reason(self) -> bool | None:
        return self._result.reason

    def get_detailed_reason(self) -> bool | None:
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

    def get_main_reason(self) -> bool | None:
        return None

    def get_detailed_reason(self) -> bool | None:
        return None
