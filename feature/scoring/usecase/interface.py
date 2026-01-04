from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from shared.domain.entity.student import StudentEntity
from shared.domain.entity.student_mark import StudentMarkEntity
from shared.domain.value.identifier import StudentID, TestCaseID
from shared.domain.value.student_stage_result import TestResultOutputFileCollection


# DTOはinterfaceの直上に定義
class StudentMarkEntityState(Enum):
    """学生採点エンティティの状態を表すEnum"""
    # ステージの処理未完了や失敗はテストケースごとの問題なのでここでは提供しない
    READY = "採点可"
    NO_TEST_FOUND = "テストケースがありません"
    RERUN_REQUIRED = "変更が検出されたため再実行が必要です"


@dataclass(slots=True)
class StudentMarkEntitySummaryViewDataDto:
    """採点サマリー表示データ取得UseCaseの結果を表すDTO"""
    student: StudentEntity
    mark: StudentMarkEntity
    state: StudentMarkEntityState
    detailed_text: str | None

    @property
    def student_id(self) -> StudentID:
        return self.student.student_id

    @property
    def is_ready(self) -> bool:
        # なんらかの理由でテストケースごとのAbstractStudentTestCaseTestResultViewDataを提供できないときFalse
        return self.state == StudentMarkEntityState.READY

    @property
    def reason(self) -> str:
        if self.is_ready:
            raise ValueError("no reason found")
        return self.state.value + ("" if self.detailed_text is None else "\n" + self.detailed_text)


class IStudentMarkGetUseCase(ABC):
    """採点データ取得UseCaseのインターフェース"""

    @abstractmethod
    def execute(self, student_id: StudentID) -> StudentMarkEntity:
        raise NotImplementedError()


class IStudentMarkPutUseCase(ABC):
    """採点データ保存UseCaseのインターフェース"""

    @abstractmethod
    def execute(self, student_mark: StudentMarkEntity) -> None:
        raise NotImplementedError()


class IStudentScoreListUseCase(ABC):
    """採点データ一覧取得UseCaseのインターフェース"""

    @abstractmethod
    def execute(self) -> list[StudentMarkEntity]:
        raise NotImplementedError()


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
    def output_and_results(self) -> TestResultOutputFileCollection:
        raise NotImplementedError()


class StudentTestCaseTestResultAcceptedViewData(AbstractStudentTestCaseTestResultViewData):
    def __init__(
            self,
            *,
            student_id: StudentID,
            testcase_id: TestCaseID,
            output_and_results: TestResultOutputFileCollection,
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
    def output_and_results(self) -> TestResultOutputFileCollection:
        return self._output_and_results


class StudentTestCaseTestResultWrongAnswerViewData(AbstractStudentTestCaseTestResultViewData):
    def __init__(
            self,
            *,
            student_id: StudentID,
            testcase_id: TestCaseID,
            output_and_results: TestResultOutputFileCollection,
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
    def output_and_results(self) -> TestResultOutputFileCollection:
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
    def output_and_results(self) -> TestResultOutputFileCollection:
        raise ValueError("output and results not provided")
        
class IStudentMarkViewDataGetTestResultUseCase(ABC):
    """テスト結果表示データ取得UseCaseのインターフェース"""

    @abstractmethod
    def execute(
            self,
            student_id: StudentID,
            testcase_id: TestCaseID,
    ) -> AbstractStudentTestCaseTestResultViewData:
        raise NotImplementedError()


class IStudentMarkViewDataGetMarkSummaryUseCase(ABC):
    """採点サマリー表示データ取得UseCaseのインターフェース"""

    @abstractmethod
    def execute(self, student_id: StudentID) -> StudentMarkEntitySummaryViewDataDto:
        raise NotImplementedError()


class IStudentSourceCodeGetUseCase(ABC):
    """学生ソースコード取得UseCaseのインターフェース"""

    @abstractmethod
    def execute(self, student_id: StudentID) -> str | None:
        raise NotImplementedError()
