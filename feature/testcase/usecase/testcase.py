from feature.testcase.usecase.interface import (
    ITestCaseConfigGetUseCase,
    ITestCaseConfigPutUseCase,
    ITestCaseConfigListIDUseCase,
)
from shared.domain.entity.testcase import TestCaseConfigEntity
from shared.domain.interface.repository import ITestCaseRepository
from shared.domain.value.identifier import TestCaseID


class TestCaseGetUseCase(ITestCaseConfigGetUseCase):
    def __init__(
            self,
            *,
            testcase_config_repo: ITestCaseRepository,
    ):
        self._testcase_config_repo = testcase_config_repo

    def execute(self, testcase_id: TestCaseID) -> TestCaseConfigEntity:
        return self._testcase_config_repo.get(testcase_id)


class TestCasePutUseCase(ITestCaseConfigPutUseCase):
    def __init__(
            self,
            *,
            testcase_config_repo: ITestCaseRepository,
    ):
        self._testcase_config_repo = testcase_config_repo

    def execute(self, testcase_config: TestCaseConfigEntity) -> None:
        self._testcase_config_repo.put(testcase_config)


class TestCaseListIDUseCase(ITestCaseConfigListIDUseCase):
    def __init__(
            self,
            *,
            testcase_config_repo: ITestCaseRepository,
    ):
        self._testcase_config_repo = testcase_config_repo

    def execute(self) -> list[TestCaseID]:
        return [
            testcase_config.testcase_id
            for testcase_config in self._testcase_config_repo.list_all()
        ]
