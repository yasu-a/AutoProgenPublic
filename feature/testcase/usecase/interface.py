from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING

from shared.domain.entity.testcase_config import TestCaseConfigEntity
from shared.domain.value.identifier import TestCaseID
from shared.domain.value.test_result_output_file_entry import AbstractTestResultOutputFileEntry

if TYPE_CHECKING:
    from shared.domain.value.expected_output_file import ExpectedOutputFile
    from shared.domain.value.test_config_options import TestConfigOptions


# DTOはinterfaceの直上に定義
@dataclass(frozen=True)
class TestCaseSummaryDto:
    """テストケース一覧取得UseCaseの結果を表すDTO"""
    testcase_id: TestCaseID
    name: str
    has_stdin: bool
    num_normal_files: int


@dataclass(slots=True)
class TestTestStageResultDto:
    """テストステージ実行UseCaseの結果を表すDTO"""
    regex_pattern: str | None  # None if error
    error_message: str | None  # None if success
    file_test_result: AbstractTestResultOutputFileEntry | None  # None if error
    test_execution_timedelta: timedelta | None  # None if error

    @property
    def has_error(self) -> bool:
        return self.error_message is not None

    @classmethod
    def create_error(
            cls,
            *,
            error_message: str,
    ):
        return cls(
            regex_pattern=None,
            error_message=error_message,
            file_test_result=None,
            test_execution_timedelta=None,
        )

    @classmethod
    def create_success(
            cls,
            *,
            regex_pattern: str,
            file_test_result: AbstractTestResultOutputFileEntry,
            test_execution_timedelta: timedelta,
    ):
        return cls(
            regex_pattern=regex_pattern,
            error_message=None,
            file_test_result=file_test_result,
            test_execution_timedelta=test_execution_timedelta,
        )


# TestCase UseCase Interfaces
class ITestCaseConfigGetUseCase(ABC):
    @abstractmethod
    def execute(self, testcase_id: TestCaseID) -> TestCaseConfigEntity:
        raise NotImplementedError()


class ITestCaseConfigPutUseCase(ABC):
    @abstractmethod
    def execute(self, testcase_config: TestCaseConfigEntity) -> None:
        raise NotImplementedError()


class ITestCaseConfigListIDUseCase(ABC):
    @abstractmethod
    def execute(self) -> list[TestCaseID]:
        raise NotImplementedError()


class ITestCaseListSummaryUseCase(ABC):
    @abstractmethod
    def execute(self) -> list[TestCaseSummaryDto]:
        raise NotImplementedError()


class ITestCaseCreateNewNameUseCase(ABC):
    @abstractmethod
    def execute(self) -> str:
        raise NotImplementedError()


class ITestCaseCreateUseCase(ABC):
    @abstractmethod
    def execute(self, testcase_name: str) -> None:
        raise NotImplementedError()


class ITestCaseCopyUseCase(ABC):
    @abstractmethod
    def execute(self, *, src_testcase_id: TestCaseID, new_testcase_name: str) -> None:
        raise NotImplementedError()


class ITestTestStageUseCase(ABC):
    @abstractmethod
    def execute(
            self,
            *,
            expected_output_file: "ExpectedOutputFile",
            test_config_options: "TestConfigOptions",
            content_text: str,
    ) -> "TestTestStageResultDto":
        raise NotImplementedError()