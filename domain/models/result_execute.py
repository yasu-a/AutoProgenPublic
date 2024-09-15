from dataclasses import dataclass
from datetime import datetime

from domain.models.output_file import OutputFileMapping
from domain.models.result_base import AbstractResult
from domain.models.values import TestCaseID


class TestCaseExecuteResult:
    def __init__(
            self,
            *,
            testcase_id: TestCaseID,
            execute_config_mtime: datetime,
            output_files: OutputFileMapping,
            reason: str | None = None,
    ):
        self._testcase_id = testcase_id
        self._execute_config_mtime = execute_config_mtime
        self._output_files = output_files
        self._reason = reason

    def to_json(self) -> dict:
        return dict(
            testcase_id=self._testcase_id.to_json(),
            execute_config_mtime=self._execute_config_mtime.isoformat(),
            output_files=self._output_files.to_json(),
            reason=self._reason,
        )

    @classmethod
    def from_json(cls, body: dict):
        return cls(
            testcase_id=TestCaseID.from_json(body["testcase_id"]),
            execute_config_mtime=datetime.fromisoformat(body.get("execute_config_mtime")),
            output_files=OutputFileMapping.from_json(body["output_files"]),
            reason=body.get("reason"),
        )

    @classmethod
    def error(
            cls,
            *,
            testcase_id: TestCaseID,
            execute_config_mtime: datetime,
            reason: str,
    ) -> "TestCaseExecuteResult":
        return cls(
            testcase_id=testcase_id,
            execute_config_mtime=execute_config_mtime,
            output_files=OutputFileMapping(),
            reason=reason,
        )

    @classmethod
    def success(
            cls,
            *,
            testcase_id: TestCaseID,
            execute_config_mtime: datetime,
            output_files: OutputFileMapping,
    ) -> "TestCaseExecuteResult":
        return cls(
            testcase_id=testcase_id,
            execute_config_mtime=execute_config_mtime,
            output_files=output_files,
            reason=None,
        )

    @property
    def testcase_id(self) -> TestCaseID:
        return self._testcase_id

    @property
    def execute_config_mtime(self) -> datetime:
        return self._execute_config_mtime

    @property
    def output_files(self) -> OutputFileMapping:
        return self._output_files

    @property
    def reason(self) -> str | None:
        return self._reason


class TestCaseExecuteResultMapping(dict[TestCaseID, TestCaseExecuteResult]):
    # TODO: frozendictを導入してこのクラスのインスタンスを持つクラスをすべてdataclass(frozen=True)にする

    def __validate(self):
        for testcase_id, testcase_execute_result in self.items():
            # キーとしてのTestCaseIDと値の中のTestCaseIDは一致する
            assert testcase_id == testcase_execute_result.testcase_id, \
                (testcase_id, testcase_execute_result)

    def to_json(self) -> dict[str, dict]:
        self.__validate()
        return {
            testcase_id.to_json(): testcase_execute_result.to_json()
            for testcase_id, testcase_execute_result in self.items()
        }

    @classmethod
    def from_json(cls, body: dict):
        obj = cls({
            TestCaseID.from_json(testcase_id_str): TestCaseExecuteResult.from_json(
                testcase_execute_result_body
            )
            for testcase_id_str, testcase_execute_result_body in body.items()
        })
        obj.__validate()
        return obj


@dataclass(slots=True)
class ExecuteResult(AbstractResult):
    testcase_results: TestCaseExecuteResultMapping

    @classmethod
    def error(cls, reason: str) -> "ExecuteResult":
        return cls(reason=reason, testcase_results=TestCaseExecuteResultMapping())

    @classmethod
    def success(cls, testcase_results: TestCaseExecuteResultMapping) -> "ExecuteResult":
        return cls(reason=None, testcase_results=testcase_results)

    def to_json(self) -> dict:
        return dict(
            reason=self.reason,
            testcase_results=self.testcase_results.to_json(),
        )

    @classmethod
    def from_json(cls, body: dict) -> "ExecuteResult":
        return cls(
            reason=body["reason"],
            testcase_results=TestCaseExecuteResultMapping.from_json(
                body["testcase_results"]),
        )
