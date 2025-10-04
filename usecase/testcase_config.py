from domain.model.testcase_config import TestCaseConfig
from domain.model.value import TestCaseID
from service.testcase_config import TestCaseConfigGetService, TestCaseConfigPutService, \
    TestCaseConfigListIDSubService


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


class TestCaseConfigListIDUseCase:
    def __init__(
            self,
            *,
            testcase_config_list_id_sub_service: TestCaseConfigListIDSubService,
    ):
        self._testcase_config_list_id_sub_service = testcase_config_list_id_sub_service

    def execute(self) -> list[TestCaseID]:
        return self._testcase_config_list_id_sub_service.execute()
