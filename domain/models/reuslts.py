from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import IntEnum

from domain.errors import BuildServiceError, CompileServiceError
from domain.models.testcase import ExecuteConfig
from domain.models.values import TestCaseID


@dataclass
class AbstractResult(ABC):
    reason: str | None

    def is_success(self) -> bool:
        return self.reason is None

    @property
    def detailed_reason(self) -> str | None:
        return self.reason

    @abstractmethod
    def to_json(self):
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def from_json(cls, body):
        raise NotImplementedError()


@dataclass
class BuildResult(AbstractResult):
    @classmethod
    def error(cls, e: BuildServiceError) -> "BuildResult":
        return cls(reason=e.reason)

    @classmethod
    def success(cls) -> "BuildResult":
        return cls(reason=None)

    def to_json(self):
        return dict(
            reason=self.reason,
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            reason=body["reason"],
        )


@dataclass
class CompileResult(AbstractResult):
    output: str | None

    @property
    def detailed_reason(self) -> str | None:
        if self.reason is None:
            return None
        return f"{self.reason}\n{self.output}"

    @classmethod
    def error(cls, e: CompileServiceError) -> "CompileResult":
        return cls(reason=e.reason, output=e.output)

    @classmethod
    def success(cls, output: str) -> "CompileResult":
        return cls(reason=None, output=output)

    def to_json(self):
        return dict(
            reason=self.reason,
            output=self.output,
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            reason=body["reason"],
            output=body["output"],
        )


class ExecuteResultFlag(IntEnum):
    EXIT_NORMALLY = 0
    EXECUTION_FAILED = 1


@dataclass(frozen=True)
class TestCaseExecuteResult:
    testcase_id: TestCaseID
    execute_config: ExecuteConfig
    flag: ExecuteResultFlag
    reason: str | None = None

    def to_json(self):
        return dict(
            testcase_id=self.testcase_id.to_json(),
            execute_config=self.execute_config.to_json(),
            flag=self.flag.value,
            reason=self.reason,
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            testcase_id=TestCaseID.from_json(body["testcase_id"]),
            execute_config=ExecuteConfig.from_json(body["execute_config"]),
            flag=ExecuteResultFlag(body["flag"]),
            reason=body["reason"],
        )

    def __hash__(self):
        return hash(self.testcase_id)


class TestCaseExecuteResultSet(set[TestCaseExecuteResult]):
    def to_json(self) -> list[dict]:
        return [
            item.to_json()
            for item in self
        ]

    @classmethod
    def from_json(cls, body: list[dict]):
        return cls({
            TestCaseExecuteResult.from_json(item)
            for item in body
        })


@dataclass(slots=True)
class ExecuteResult(AbstractResult):
    testcase_result_set: TestCaseExecuteResultSet

    @classmethod
    def success(cls, testcase_result_set: TestCaseExecuteResultSet) -> "ExecuteResult":
        return cls(reason=None, testcase_result_set=testcase_result_set)

    def to_json(self):
        return dict(
            reason=self.reason,
            testcase_result_set=self.testcase_result_set.to_json(),
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            reason=body["reason"],
            testcase_result_set=TestCaseExecuteResultSet.from_json(body["testcase_result_set"]),
        )
