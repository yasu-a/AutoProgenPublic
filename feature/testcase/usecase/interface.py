from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from feature.testcase.usecase.dto import TestCaseSummary
from shared.domain.entity.testcase_config import TestCaseConfigEntity
from shared.domain.value.identifier import TestCaseID

if TYPE_CHECKING:
    from feature.testcase.usecase.dto import TestTestStageResult
    from shared.domain.value.expected_output_file import ExpectedOutputFile
    from shared.domain.value.test_config_options import TestConfigOptions


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
    def execute(self) -> list[TestCaseSummary]:
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
    ) -> "TestTestStageResult":
        raise NotImplementedError()