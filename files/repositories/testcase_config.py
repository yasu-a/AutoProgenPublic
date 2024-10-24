from typing import Iterable

from domain.models.execute_config import TestCaseExecuteConfig
from domain.models.test_config import TestCaseTestConfig
from domain.models.testcase_config import TestCaseConfig
from domain.models.values import TestCaseID
from files.core.current_project import CurrentProjectCoreIO
from files.path_providers.current_project import TestCaseConfigPathProvider
from transaction import transactional_with, transactional


class TestCaseConfigRepository:
    def __init__(
            self,
            *,
            testcase_config_path_provider: TestCaseConfigPathProvider,
            current_project_core_io: CurrentProjectCoreIO,
    ):
        self._testcase_config_path_provider = testcase_config_path_provider
        self._current_project_core_io = current_project_core_io

    def __ensure_testcase_folder_exists(self, testcase_id: TestCaseID) -> None:
        testcase_folder_fullpath = self._testcase_config_path_provider.testcase_folder_fullpath(
            testcase_id)
        testcase_folder_fullpath.mkdir(parents=True, exist_ok=True)

    def __iter_testcase_folder_names(self) -> Iterable[str]:
        base_folder_fullpath = self._testcase_config_path_provider.base_folder_fullpath()
        base_folder_fullpath.mkdir(parents=True, exist_ok=True)
        for testcase_folder_fullpath in base_folder_fullpath.iterdir():
            if not testcase_folder_fullpath.is_dir():
                continue
            folder_name = testcase_folder_fullpath.name
            yield folder_name

    def __write_execute_config(
            self,
            testcase_id: TestCaseID,
            execute_config: TestCaseExecuteConfig,
    ) -> None:
        self.__ensure_testcase_folder_exists(testcase_id)
        json_fullpath = self._testcase_config_path_provider.execute_config_json_fullpath(
            testcase_id=testcase_id,
        )
        self._current_project_core_io.write_json(
            json_fullpath=json_fullpath,
            body=execute_config.to_json(),
        )

    def __write_test_config(
            self,
            testcase_id: TestCaseID,
            test_config: TestCaseTestConfig,
    ) -> None:
        self.__ensure_testcase_folder_exists(testcase_id)
        json_fullpath = self._testcase_config_path_provider.test_config_json_fullpath(
            testcase_id=testcase_id,
        )
        self._current_project_core_io.write_json(
            json_fullpath=json_fullpath,
            body=test_config.to_json(),
        )

    @transactional_with(testcase_id=lambda args: args["testcase_config"].testcase_id)
    def put(self, testcase_config: TestCaseConfig):
        self.__write_execute_config(
            testcase_id=testcase_config.testcase_id,
            execute_config=testcase_config.execute_config,
        )
        self.__write_test_config(
            testcase_id=testcase_config.testcase_id,
            test_config=testcase_config.test_config,
        )

    def __read_execute_config(self, testcase_id: TestCaseID) -> TestCaseExecuteConfig:
        json_fullpath = self._testcase_config_path_provider.execute_config_json_fullpath(
            testcase_id=testcase_id,
        )
        if not json_fullpath.exists():
            raise FileNotFoundError("Execute config file does not exist")
        json_body = self._current_project_core_io.read_json(json_fullpath=json_fullpath)
        return TestCaseExecuteConfig.from_json(json_body)

    def __read_test_config(self, testcase_id: TestCaseID) -> TestCaseTestConfig:
        json_fullpath = self._testcase_config_path_provider.test_config_json_fullpath(
            testcase_id=testcase_id,
        )
        if not json_fullpath.exists():
            raise FileNotFoundError("Test config file does not exist")
        json_body = self._current_project_core_io.read_json(json_fullpath=json_fullpath)
        return TestCaseTestConfig.from_json(json_body)

    @transactional_with("testcase_id")
    def exists(self, testcase_id: TestCaseID) -> bool:
        return any(
            str(testcase_id) in testcase_folder_name
            for testcase_folder_name in self.__iter_testcase_folder_names()
        )

    @transactional_with("testcase_id")
    def get(self, testcase_id: TestCaseID) -> TestCaseConfig:
        execute_config = self.__read_execute_config(testcase_id=testcase_id)
        test_config = self.__read_test_config(testcase_id=testcase_id)
        return TestCaseConfig(
            testcase_id=testcase_id,
            execute_config=execute_config,
            test_config=test_config,
        )

    @transactional
    def list(self) -> list[TestCaseConfig]:
        return [
            self.get(TestCaseID(folder_name))
            for folder_name in self.__iter_testcase_folder_names()
        ]

    def __delete_execute_config(self, testcase_id: TestCaseID) -> None:
        json_fullpath = self._testcase_config_path_provider.execute_config_json_fullpath(
            testcase_id=testcase_id,
        )
        if not json_fullpath.exists():
            raise FileNotFoundError("Execute config file does not exist")
        self._current_project_core_io.unlink(
            path=json_fullpath,
        )

    def __delete_test_config(self, testcase_id: TestCaseID) -> None:
        json_fullpath = self._testcase_config_path_provider.test_config_json_fullpath(
            testcase_id=testcase_id,
        )
        if not json_fullpath.exists():
            raise FileNotFoundError("Test config file does not exist")
        self._current_project_core_io.unlink(
            path=json_fullpath,
        )

    @transactional_with("testcase_id")
    def delete(self, testcase_id: TestCaseID) -> None:
        self.__delete_execute_config(testcase_id=testcase_id)
        self.__delete_test_config(testcase_id=testcase_id)
