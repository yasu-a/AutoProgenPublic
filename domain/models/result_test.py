from dataclasses import dataclass
from enum import Enum

from domain.models.result_base import AbstractResult
from domain.models.testcase import TestConfig
from domain.models.values import TestCaseID


class TestSummary(Enum):
    WRONG_ANSWER = "正解条件を満たしていません"
    ACCEPTED = "正解です"
    UNTESTED = "テストできません"

    @classmethod
    def get_abbreviations(cls, value: "TestSummary"):
        return _test_indicator_abbreviations[value]


_test_indicator_abbreviations = {
    TestSummary.WRONG_ANSWER: "WA",
    TestSummary.ACCEPTED: "AC",
    TestSummary.UNTESTED: "NA",
}


@dataclass(frozen=True)
class TestCaseTestResult:
    testcase_id: TestCaseID  # TODO: dictにしても残しておいたほうがいい
    test_config: TestConfig
    summary: TestSummary

    def to_json(self):
        return dict(
            testcase_id=self.testcase_id.to_json(),
            test_config=self.test_config.to_json(),
            summary=self.summary.value,
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            testcase_id=TestCaseID.from_json(body["testcase_id"]),
            test_config=TestConfig.from_json(body["test_config"]),
            summary=TestSummary(body["summary"]),
        )

    def __hash__(self):
        return hash(self.testcase_id)


class TestCaseTestResultSet(set[TestCaseTestResult]):  # TODO: dictにする
    def to_json(self) -> list[dict]:
        return [
            item.to_json()
            for item in self
        ]

    @classmethod
    def from_json(cls, body: list[dict]):
        return cls({
            TestCaseTestResult.from_json(item)
            for item in body
        })


@dataclass(slots=True)
class TestResult(AbstractResult):  # TODO: Testはステージに属さないのでAbstractResultは継承しない
    testcase_result_set: TestCaseTestResultSet

    @classmethod
    def error(cls, reason: str) -> "TestResult":
        raise ValueError("Test never fails")

    @classmethod
    def success(cls, testcase_result_set: TestCaseTestResultSet) -> "TestResult":
        return cls(reason=None, testcase_result_set=testcase_result_set)

    def to_json(self):
        return dict(
            reason=self.reason,
            testcase_result_set=(
                None
                if self.testcase_result_set is None
                else self.testcase_result_set.to_json()
            ),
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            reason=body["reason"],
            testcase_result_set=(
                None
                if body["testcase_result_set"] is None
                else TestCaseTestResultSet.from_json(body["testcase_result_set"])
            ),
        )
