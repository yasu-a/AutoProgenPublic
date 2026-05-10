from domain.model.testcase_config import TestCaseConfig
from domain.model.value import TestCaseID
from infra.repository.testcase_config import TestCaseConfigRepository
from service.testcase_config import TestCaseConfigListIDSubService


class TestCaseConfigGetUseCase:
    def __init__(
            self,
            *,
            testcase_config_repo: TestCaseConfigRepository,
    ):
        self._testcase_config_repo = testcase_config_repo

    def execute(self, testcase_id: TestCaseID) -> TestCaseConfig:
        return self._testcase_config_repo.get(testcase_id)


class TestCaseConfigPutUseCase:
    def __init__(
            self,
            *,
            testcase_config_repo: TestCaseConfigRepository,
    ):
        self._testcase_config_repo = testcase_config_repo

    def execute(self, testcase_config: TestCaseConfig) -> None:
        self._testcase_config_repo.put(testcase_config)


class TestCaseConfigListIDUseCase:
    def __init__(
            self,
            *,
            testcase_config_list_id_sub_service: TestCaseConfigListIDSubService,
    ):
        self._testcase_config_list_id_sub_service = testcase_config_list_id_sub_service

    def execute(self) -> list[TestCaseID]:
        return self._testcase_config_list_id_sub_service.execute()


class TestCaseConfigDeleteUseCase:
    def __init__(
            self,
            *,
            testcase_config_repo: TestCaseConfigRepository,
    ):
        self._testcase_config_repo = testcase_config_repo

    def execute(self, testcase_id: TestCaseID) -> None:
        self._testcase_config_repo.delete(testcase_id)
