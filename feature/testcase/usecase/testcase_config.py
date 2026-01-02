from feature.testcase.usecase.interface import (
    ITestCaseConfigGetUseCase,
    ITestCaseConfigPutUseCase,
    ITestCaseConfigListIDUseCase,
)
from shared.domain.entity.testcase_config import TestCaseConfigEntity
from shared.domain.value.identifier import TestCaseID
from shared.infra.repository.testcase_config import TestCaseConfigRepository


class TestCaseConfigGetUseCase(ITestCaseConfigGetUseCase):
    def __init__(
            self,
            *,
            testcase_config_repo: TestCaseConfigRepository,
    ):
        self._testcase_config_repo = testcase_config_repo

    def execute(self, testcase_id: TestCaseID) -> TestCaseConfigEntity:
        return self._testcase_config_repo.get(testcase_id)


class TestCaseConfigPutUseCase(ITestCaseConfigPutUseCase):
    def __init__(
            self,
            *,
            testcase_config_repo: TestCaseConfigRepository,
    ):
        self._testcase_config_repo = testcase_config_repo

    def execute(self, testcase_config: TestCaseConfigEntity) -> None:
        self._testcase_config_repo.put(testcase_config)


class TestCaseConfigListIDUseCase(ITestCaseConfigListIDUseCase):
    def __init__(
            self,
            *,
            testcase_config_repo: TestCaseConfigRepository,
    ):
        self._testcase_config_repo = testcase_config_repo

    def execute(self) -> list[TestCaseID]:
        return [
            testcase_config.testcase_id
            for testcase_config in self._testcase_config_repo.list()
        ]
