from domain.model.testcase_config import TestCaseConfig
from domain.model.value import TestCaseID
from infra.repository.testcase_config import TestCaseConfigRepository


class TestCaseGetUseCase:
    def __init__(
            self,
            *,
            testcase_config_repo: TestCaseConfigRepository,
    ):
        self._testcase_config_repo = testcase_config_repo

    def execute(self, testcase_id: TestCaseID) -> TestCaseConfig:
        return self._testcase_config_repo.get(testcase_id)


class TestCasePutUseCase:
    def __init__(
            self,
            *,
            testcase_config_repo: TestCaseConfigRepository,
    ):
        self._testcase_config_repo = testcase_config_repo

    def execute(self, testcase_config: TestCaseConfig) -> None:
        self._testcase_config_repo.put(testcase_config)


class TestCaseListIDUseCase:
    def __init__(
            self,
            *,
            testcase_config_repo: TestCaseConfigRepository,
    ):
        self._testcase_config_repo = testcase_config_repo

    def execute(self) -> list[TestCaseID]:
        return self._testcase_config_repo.list_ids()


class TestCaseDeleteUseCase:
    def __init__(
            self,
            *,
            testcase_config_repo: TestCaseConfigRepository,
    ):
        self._testcase_config_repo = testcase_config_repo

    def execute(self, testcase_id: TestCaseID) -> None:
        self._testcase_config_repo.delete(testcase_id)
