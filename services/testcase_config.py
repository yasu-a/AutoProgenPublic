from datetime import datetime

from domain.models.execute_config_options import ExecuteConfigOptions
from domain.models.test_config_options import TestConfigOptions
from domain.models.values import TestCaseID
from files.repositories.testcase_config import TestCaseConfigRepository


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


class TestCaseConfigGetExecuteOptionsService:
    def __init__(
            self,
            testcase_config_repo: TestCaseConfigRepository,
    ):
        self._testcase_config_repo = testcase_config_repo

    def execute(self, testcase_id: TestCaseID) -> ExecuteConfigOptions:
        return self._testcase_config_repo.get(testcase_id).execute_config.options


class TestCaseConfigGetTestOptionsService:
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
