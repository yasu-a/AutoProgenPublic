from dataclasses import dataclass, asdict
from enum import Enum


@dataclass(slots=True)
class TestCaseConfig:
    allow_spaces_start_of_line: bool
    allow_spaces_end_of_line: bool
    allow_multiple_spaces_between_words: bool
    allow_empty_lines: bool
    allow_letter_case_difference: bool
    allowable_line_levenshtein_distance: int
    timeout: float

    def __post_init__(self):
        if not isinstance(self.allow_spaces_start_of_line, bool):
            raise TypeError()
        if not isinstance(self.allow_spaces_end_of_line, bool):
            raise TypeError()
        if not isinstance(self.allow_multiple_spaces_between_words, bool):
            raise TypeError()
        if not isinstance(self.allow_empty_lines, bool):
            raise TypeError()
        if not isinstance(self.allow_letter_case_difference, bool):
            raise TypeError()
        if not isinstance(self.allowable_line_levenshtein_distance, int):
            raise TypeError()
        if isinstance(self.timeout, int):
            self.timeout = float(self.timeout)
        if not isinstance(self.timeout, float):
            raise TypeError()

    @classmethod
    def create_empty(cls):
        return cls(
            allow_spaces_start_of_line=True,
            allow_spaces_end_of_line=True,
            allow_empty_lines=True,
            allow_multiple_spaces_between_words=True,
            allow_letter_case_difference=True,
            allowable_line_levenshtein_distance=0,
            timeout=3.0,
        )

    def to_json(self):
        return asdict(self)

    @classmethod
    def from_json(cls, body):
        return cls(
            allow_spaces_start_of_line=body["allow_spaces_start_of_line"],
            allow_spaces_end_of_line=body["allow_spaces_end_of_line"],
            allow_multiple_spaces_between_words=body["allow_multiple_spaces_between_words"],
            allow_empty_lines=body["allow_empty_lines"],
            allow_letter_case_difference=body["allow_letter_case_difference"],
            allowable_line_levenshtein_distance=body["allowable_line_levenshtein_distance"],
            timeout=body["timeout"],
        )


@dataclass(slots=True)
class TestCase:
    expected_input_lines: list[str]
    expected_output_lines: list[str]
    config: TestCaseConfig
    number: int

    def to_json(self):
        return dict(
            expected_input_lines=self.expected_input_lines,
            expected_output_lines=self.expected_output_lines,
            config=self.config.to_json(),
            number=self.number,
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            expected_input_lines=body["expected_input_lines"],
            expected_output_lines=body["expected_output_lines"],
            config=TestCaseConfig.from_json(body["config"]),
            number=body["number"],
        )

    @property
    def expected_input(self) -> str:
        return "\n".join(self.expected_input_lines)

    @expected_input.setter
    def expected_input(self, value: str):
        self.expected_input_lines = value.replace("\r\n", "\n").split("\n")

    @property
    def expected_output(self) -> str:
        return "\n".join(self.expected_output_lines)

    @expected_output.setter
    def expected_output(self, value: str):
        self.expected_output_lines = value.replace("\r\n", "\n").split("\n")

    @classmethod
    def create_empty(cls, number: int):
        return cls(
            expected_input_lines=[],
            expected_output_lines=[],
            config=TestCaseConfig.create_empty(),
            number=number
        )

    def is_effectively_empty(self) -> bool:
        return not self.expected_input.strip() and not self.expected_output.strip()

    def has_output(self) -> bool:
        return bool(self.expected_output)

    def has_input(self) -> bool:
        return bool(self.expected_input)


class TestCaseResultState(Enum):
    OK = "OK"
    NO_BUILD_FOUND = "NF"
    EXECUTION_TIMEOUT = "TO"
    WRONG_ANSWER = "WA"


@dataclass(slots=True)
class TestCaseResult:
    testcase: TestCase
    actual_output_lines: list[str] | None
    result_state: TestCaseResultState

    def to_json(self):
        return dict(
            testcase=self.testcase.to_json(),
            actual_output_lines=self.actual_output_lines,
            result_state=self.result_state.value,
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            testcase=TestCase.from_json(body["testcase"]),
            actual_output_lines=body["actual_output_lines"],
            result_state=TestCaseResultState(body["result_state"]),
        )

    @property
    def actual_output(self) -> str:
        return "\n".join(self.actual_output_lines)


@dataclass(slots=True)
class TestSession:
    testcases: list[TestCase]  # TODO: testcases are unordered

    def to_json(self):
        return dict(
            testcases=[
                v.to_json()
                for v in self.testcases
            ],
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            testcases=[
                TestCase.from_json(v)
                for v in body["testcases"]
            ],
        )

    @classmethod
    def create_empty(cls):
        return cls(
            testcases=[],
        )

    def get_testcase_by_number(self, testcase_number: int) -> TestCase | None:
        for testcase in self.testcases:
            if testcase.number == testcase_number:
                return testcase
        return None

    def is_effectively_empty(self) -> bool:
        return all(testcase.is_effectively_empty() for testcase in self.testcases)

    def has_no_testcases(self) -> bool:
        return len(self.testcases) == 0

@dataclass(slots=True)
class TestSessionResult:
    testcase_results: list[TestCaseResult] | None
    reason: str | None

    def to_json(self):
        return dict(
            testcase_results=(
                None
                if self.testcase_results is None
                else [
                    v.to_json()
                    for v in self.testcase_results
                ]
            ),
            reason=self.reason,
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            testcase_results=(
                None
                if body["testcase_results"] is None
                else [
                    TestCaseResult.from_json(v)
                    for v in body["testcase_results"]
                ]
            ),
            reason=body["reason"],
        )

    @property
    def success(self) -> bool:
        return self.reason is None

    def testcase_results_string(self) -> str | None:
        if self.testcase_results is None:
            return None
        return " ".join(
            testcase_result.result_state.value
            for testcase_result in self.testcase_results
        )


@dataclass(slots=True)
class StudentTestResult:
    test_session_results: dict[int, TestSessionResult]  # target_index -> TestSessionResult

    def to_json(self):
        return dict(
            test_session_results={
                k: v.to_json()
                for k, v in self.test_session_results.items()
            },
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            test_session_results={
                int(k): TestSessionResult.from_json(v)
                for k, v in body["test_session_results"].items()
            },
        )

    @property
    def success(self) -> bool:
        return all(
            test_session_result.success
            for test_session_result in self.test_session_results.values()
        )

    @property
    def main_reason(self) -> str | None:
        for test_session_result in self.test_session_results.values():
            if not test_session_result.success:
                return test_session_result.reason
        return None

    @property
    def testcase_result_string(self) -> str:
        text_lst = []
        for i_target, test_session_result in self.test_session_results.items():
            text_lst.append(
                f"{i_target:02}: {test_session_result.testcase_results_string()}"
            )
        return " / ".join(text_lst)
