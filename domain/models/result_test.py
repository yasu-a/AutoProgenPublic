from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from domain.models.result_base import AbstractResult
from domain.models.values import TestCaseID, FileID


@dataclass(slots=True)
class MatchedToken:
    match_begin: int
    match_end: int
    expected_token_index: int

    def to_json(self) -> dict:
        return dict(
            match_begin=self.match_begin,
            match_end=self.match_end,
            expected_token_index=self.expected_token_index,
        )

    @classmethod
    def from_json(cls, body: dict) -> "MatchedToken":
        return cls(
            match_begin=body["match_begin"],
            match_end=body["match_end"],
            expected_token_index=body["expected_token_index"],
        )


@dataclass(slots=True)
class NonmatchedToken:
    expected_token_index: int

    def to_json(self) -> dict:
        return dict(
            expected_token_index=self.expected_token_index,
        )

    @classmethod
    def from_json(cls, body: dict) -> "NonmatchedToken":
        return cls(
            expected_token_index=body["expected_token_index"],
        )


@dataclass(slots=True)
class OutputFileTestResult:
    file_id: FileID
    matched_tokens: list[MatchedToken]
    nonmatched_tokens: list[NonmatchedToken]

    def to_json(self) -> dict:
        return dict(
            file_id=self.file_id.to_json(),
            matched_tokens=[token.to_json() for token in self.matched_tokens],
            nonmatched_tokens=[token.to_json() for token in self.nonmatched_tokens],
        )

    @classmethod
    def from_json(cls, body: dict) -> "OutputFileTestResult":
        return cls(
            file_id=FileID.from_json(body["file_id"]),
            matched_tokens=[
                MatchedToken.from_json(token_body)
                for token_body in body["matched_tokens"]
            ],
            nonmatched_tokens=[
                NonmatchedToken.from_json(token_body)
                for token_body in body["nonmatched_tokens"]
            ],
        )

    @property
    def is_accepted(self) -> bool:  # 正解かどうか
        return len(self.nonmatched_tokens) == 0


class OutputFileTestResultMapping(dict[FileID, OutputFileTestResult | None]):  # 出力ファイルがない場合はNone
    def to_json(self) -> dict[str, dict]:
        return {
            file_id.to_json(): (
                result.to_json()
                if result is not None
                else None
            )
            for file_id, result in self.items()
        }

    @classmethod
    def from_json(cls, body: dict) -> "OutputFileTestResultMapping":
        return cls({
            FileID.from_json(file_id_str): (
                None
                if result_body is None
                else OutputFileTestResult.from_json(result_body)
            )
            for file_id_str, result_body in body.items()
        })

    @property
    def is_accepted(self) -> bool:  # テストケースが正解かどうか（全ての出力が正解かどうか）
        return all(result is not None and result.is_accepted for result in self.values())


class TestSummary(Enum):
    WRONG_ANSWER = "正解条件を満たしていません"
    ACCEPTED = "正解です"
    UNTESTABLE = "テストできません"


class TestCaseTestResult:
    def __init__(
            self,
            *,
            testcase_id: TestCaseID,
            test_config_mtime: datetime,
            output_file_test_results: OutputFileTestResultMapping,
            reason: str | None = None,
    ):
        self._testcase_id = testcase_id
        self._test_config_mtime = test_config_mtime
        self._output_file_test_results = output_file_test_results
        self._reason = reason

    def to_json(self) -> dict:
        return dict(
            testcase_id=self._testcase_id.to_json(),
            test_config_mtime=self._test_config_mtime,
            output_file_test_results=self._output_file_test_results.to_json(),
            reason=self._reason,
        )

    @classmethod
    def from_json(cls, body: dict):
        return cls(
            testcase_id=TestCaseID.from_json(body["testcase_id"]),
            test_config_mtime=body.get("test_config_mtime"),
            output_file_test_results=OutputFileTestResultMapping.from_json(
                body["output_file_test_results"],
            ),
            reason=body.get("reason"),
        )

    @classmethod
    def error(
            cls,
            *,
            testcase_id: TestCaseID,
            test_config_mtime: datetime,
            reason: str,
    ) -> "TestCaseTestResult":
        return cls(
            testcase_id=testcase_id,
            test_config_mtime=test_config_mtime,
            output_file_test_results=OutputFileTestResultMapping(),
            reason=reason,
        )

    @classmethod
    def success(
            cls,
            *,
            testcase_id: TestCaseID,
            test_config_mtime: datetime,
            output_file_test_results: OutputFileTestResultMapping,
    ) -> "TestCaseTestResult":
        return cls(
            testcase_id=testcase_id,
            test_config_mtime=test_config_mtime,
            output_file_test_results=output_file_test_results,
            reason=None,
        )

    @property
    def testcase_id(self) -> TestCaseID:
        return self._testcase_id

    @property
    def test_config_mtime(self) -> datetime:
        return self._test_config_mtime

    @property
    def output_file_test_results(self) -> OutputFileTestResultMapping:
        return self._output_file_test_results

    @property
    def reason(self) -> str | None:
        return self._reason

    @property
    def is_success(self) -> bool:
        return self._reason is None

    @property
    def summary(self) -> TestSummary:
        if self.is_success:
            if self.output_file_test_results.is_accepted:
                return TestSummary.ACCEPTED
            else:
                return TestSummary.WRONG_ANSWER
        else:
            return TestSummary.UNTESTABLE


class TestCaseTestResultMapping(dict[TestCaseID, TestCaseTestResult]):
    def to_json(self) -> dict[str, dict]:
        return {
            testcase_id.to_json(): testcase_result.to_json()
            for testcase_id, testcase_result in self.items()
        }

    @classmethod
    def from_json(cls, body: dict):
        return cls(
            {
                TestCaseID.from_json(testcase_id_str): TestCaseTestResult.from_json(
                    testcase_result_body
                )
                for testcase_id_str, testcase_result_body in body.items()
            }
        )


@dataclass(slots=True)
class TestResult(AbstractResult):
    testcase_results: TestCaseTestResultMapping

    @classmethod
    def error(cls, reason: str) -> "TestResult":
        return cls(reason=reason, testcase_results=TestCaseTestResultMapping())

    @classmethod
    def success(cls, testcase_results: TestCaseTestResultMapping) -> "TestResult":
        return cls(reason=None, testcase_results=testcase_results)

    def to_json(self) -> dict:
        return dict(
            reason=self.reason,
            testcase_results=self.testcase_results.to_json(),
        )

    @classmethod
    def from_json(cls, body: dict) -> "TestResult":
        return cls(
            reason=body["reason"],
            testcase_results=TestCaseTestResultMapping.from_json(
                body["testcase_results"]),
        )
