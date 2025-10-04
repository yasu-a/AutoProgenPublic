import copy
from datetime import datetime

from domain.error import ServiceError
from domain.model.execute_config_options import ExecuteConfigOptions
from domain.model.test_config_options import TestConfigOptions
from domain.model.testcase_config import TestCaseConfig
from domain.model.value import TestCaseID
from infra.repository.testcase_config import TestCaseConfigRepository


class TestCaseConfigListIDSubService:
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


class TestCaseConfigGetService:
    def __init__(
            self,
            *,
            testcase_config_repo: TestCaseConfigRepository,
    ):
        self._testcase_config_repo = testcase_config_repo

    def execute(self, testcase_id: TestCaseID) -> TestCaseConfig:
        return self._testcase_config_repo.get(testcase_id)


class TestCaseConfigPutService:
    def __init__(
            self,
            *,
            testcase_config_repo: TestCaseConfigRepository,
    ):
        self._testcase_config_repo = testcase_config_repo

    def execute(self, testcase_config: TestCaseConfig) -> None:
        self._testcase_config_repo.put(testcase_config)


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


class TestCaseConfigGetExecuteOptionsService:  # TODO remove this; use TestCaseConfigGetService
    def __init__(
            self,
            *,
            testcase_config_repo: TestCaseConfigRepository,
    ):
        self._testcase_config_repo = testcase_config_repo

    def execute(self, testcase_id: TestCaseID) -> ExecuteConfigOptions:
        return self._testcase_config_repo.get(testcase_id).execute_config.options


class TestCaseConfigGetTestOptionsService:  # TODO remove this; use TestCaseConfigGetService
    def __init__(
            self,
            testcase_config_repo: TestCaseConfigRepository,
    ):
        self._testcase_config_repo = testcase_config_repo

    def execute(self, testcase_id: TestCaseID) -> TestConfigOptions:
        return self._testcase_config_repo.get(testcase_id).test_config.options


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


class TestCaseConfigDeleteService:
    def __init__(
            self,
            testcase_config_repo: TestCaseConfigRepository,
    ):
        self._testcase_config_repo = testcase_config_repo

    def execute(self, testcase_id: TestCaseID) -> None:
        self._testcase_config_repo.delete(testcase_id)
