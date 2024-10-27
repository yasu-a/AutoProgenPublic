from domain.models.testcase_config import TestCaseConfig
from domain.models.values import TestCaseID
from services.testcase_config import TestCaseConfigGetService, TestCaseConfigPutService


class TestCaseConfigGetUseCase:
    def __init__(
            self,
            *,
            testcase_config_get_service: TestCaseConfigGetService,
    ):
        self._testcase_config_get_service = testcase_config_get_service

    def execute(self, testcase_id: TestCaseID) -> TestCaseConfig:
        return self._testcase_config_get_service.execute(testcase_id)


class TestCaseConfigPutUseCase:
    def __init__(
            self,
            *,
            testcase_config_put_service: TestCaseConfigPutService,
    ):
        self._testcase_config_put_service = testcase_config_put_service

    def execute(self, testcase_config: TestCaseConfig) -> None:
        self._testcase_config_put_service.execute(testcase_config)
