from abc import ABC, abstractmethod

from feature.scoring.usecase.dto import (
    AbstractStudentTestCaseTestResultViewData,
    StudentMarkEntitySummaryViewData,
)
from shared.domain.entity.student_mark import StudentMarkEntity
from shared.domain.value.identifier import StudentID, TestCaseID


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


class IStudentMarkListUseCase(ABC):
    """採点データ一覧取得UseCaseのインターフェース"""

    @abstractmethod
    def execute(self) -> list[StudentMarkEntity]:
        raise NotImplementedError()


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
    def execute(self, student_id: StudentID) -> StudentMarkEntitySummaryViewData:
        raise NotImplementedError()


class IStudentSourceCodeGetUseCase(ABC):
    """学生ソースコード取得UseCaseのインターフェース"""

    @abstractmethod
    def execute(self, student_id: StudentID) -> str | None:
        raise NotImplementedError()