from domain.models.values import TestCaseID
from services.testcase_config import TestCaseConfigListIDSubService


class TestCaseConfigListIDUseCase:
    def __init__(
            self,
            *,
            testcase_config_list_id_sub_service: TestCaseConfigListIDSubService,
    ):
        self._testcase_config_list_id_sub_service = testcase_config_list_id_sub_service

    def execute(self) -> list[TestCaseID]:
        return self._testcase_config_list_id_sub_service.execute()
