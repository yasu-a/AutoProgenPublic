import copy
from datetime import datetime

from domain.error import ServiceError
from domain.model.value import TestCaseID
from infra.repository.testcase_config import TestCaseConfigRepository


class TestCaseConfigCopyService:
    def __init__(
            self,
            *,
            testcase_config_repo: TestCaseConfigRepository,
    ):
        self._testcase_config_repo = testcase_config_repo

    def execute(self, testcase_id: TestCaseID, new_testcase_id: TestCaseID) -> None:
        if self._testcase_config_repo.exists(new_testcase_id):
            raise ServiceError(f"testcase_id {new_testcase_id} already exists")
        testcase_config = copy.deepcopy(self._testcase_config_repo.get(testcase_id))
        testcase_config.testcase_id = new_testcase_id
        self._testcase_config_repo.put(testcase_config)


class TestCaseConfigGetExecuteConfigMtimeService:
    def __init__(
            self,
            testcase_config_repo: TestCaseConfigRepository,
    ):
        self._testcase_config_repo = testcase_config_repo

    def execute(self, testcase_id: TestCaseID) -> datetime:
        return self._testcase_config_repo.get(testcase_id).execute_config.mtime


class TestCaseConfigGetTestConfigMtimeService:
    def __init__(
            self,
            testcase_config_repo: TestCaseConfigRepository,
    ):
        self._testcase_config_repo = testcase_config_repo

    def execute(self, testcase_id: TestCaseID) -> datetime:
        return self._testcase_config_repo.get(testcase_id).test_config.mtime
