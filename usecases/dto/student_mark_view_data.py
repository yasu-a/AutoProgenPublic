from abc import abstractmethod, ABC
from dataclasses import dataclass
from enum import Enum

from domain.models.student_mark import StudentMark
from domain.models.student_master import Student
from domain.models.student_stage_result import TestResultOutputFileMapping
from domain.models.values import StudentID, TestCaseID


class StudentTestCaseSummaryState(Enum):
    WRONG_ANSWER = "正解条件を満たしていません"
    ACCEPTED = "正解です"
    UNTESTABLE = "テストできません"


class AbstractStudentTestCaseTestResultViewData(ABC):
    def __init__(
            self,
            *,
            student_id: StudentID,
            testcase_id: TestCaseID,
    ):
        self._student_id = student_id
        self._testcase_id = testcase_id

    @property
    def student_id(self) -> StudentID:
        return self._student_id

    @property
    def testcase_id(self) -> TestCaseID:
        return self._testcase_id

    @property
    @abstractmethod
    def state(self) -> StudentTestCaseSummaryState:
        raise NotImplementedError()

    @property
    @abstractmethod
    def title_text(self) -> str:
        raise NotImplementedError()

    @property
    @abstractmethod
    def is_success(self) -> bool:
        raise NotImplementedError()

    @property
    @abstractmethod
    def detailed_reason(self) -> str:
        raise NotImplementedError()

    @property
    @abstractmethod
    def output_and_results(self) -> TestResultOutputFileMapping:
        raise NotImplementedError()


class StudentTestCaseTestResultAcceptedViewData(AbstractStudentTestCaseTestResultViewData):
    def __init__(
            self,
            *,
            student_id: StudentID,
            testcase_id: TestCaseID,
            output_and_results: TestResultOutputFileMapping,
    ):
        super().__init__(
            student_id=student_id,
            testcase_id=testcase_id,
        )
        self._output_and_results = output_and_results

    @property
    def state(self) -> StudentTestCaseSummaryState:
        return StudentTestCaseSummaryState.ACCEPTED

    @property
    def title_text(self) -> str:
        return self.state.value

    @property
    def is_success(self) -> bool:
        return True

    @property
    def detailed_reason(self) -> str:
        raise ValueError("detailed reason not provided")

    @property
    def output_and_results(self) -> TestResultOutputFileMapping:
        return self._output_and_results


class StudentTestCaseTestResultWrongAnswerViewData(AbstractStudentTestCaseTestResultViewData):
    def __init__(
            self,
            *,
            student_id: StudentID,
            testcase_id: TestCaseID,
            output_and_results: TestResultOutputFileMapping,
    ):
        super().__init__(
            student_id=student_id,
            testcase_id=testcase_id,
        )
        self._output_and_results = output_and_results

    @property
    def state(self) -> StudentTestCaseSummaryState:
        return StudentTestCaseSummaryState.WRONG_ANSWER

    @property
    def title_text(self) -> str:
        return self.state.value

    @property
    def is_success(self) -> bool:
        return True

    @property
    def detailed_reason(self) -> str:
        raise ValueError("detailed reason not provided")

    @property
    def output_and_results(self) -> TestResultOutputFileMapping:
        return self._output_and_results


class StudentTestCaseTestResultUntestableViewData(AbstractStudentTestCaseTestResultViewData):
    def __init__(
            self,
            *,
            student_id: StudentID,
            testcase_id: TestCaseID,
            reason: str,
    ):
        super().__init__(
            student_id=student_id,
            testcase_id=testcase_id,
        )
        self._reason = reason

    @property
    def state(self) -> StudentTestCaseSummaryState:
        return StudentTestCaseSummaryState.UNTESTABLE

    @property
    def is_success(self) -> bool:
        return False

    @property
    def title_text(self) -> str:
        return self.state.value

    @property
    def detailed_reason(self) -> str:
        return self._reason

    @property
    def output_and_results(self) -> TestResultOutputFileMapping:
        raise ValueError("output and results not provided")


class StudentMarkState(Enum):
    READY = "採点可"
    NO_TEST_FOUND = "テストケースがありません"
    STAGES_UNFINISHED = "すべての処理が完了していません"
    STAGES_FAILED = "処理に失敗しました"
    RERUN_REQUIRED = "変更が検出されたため再実行が必要です"


@dataclass(slots=True)
class StudentMarkSummaryViewData:
    student_id: StudentID
    student: Student
    mark: StudentMark
    state: StudentMarkState

    @property
    def is_ready(self) -> bool:
        return self.state == StudentMarkState.READY

    @property
    def reason(self) -> str:
        if self.is_ready:
            raise ValueError("no reason found")
        return self.state.value
