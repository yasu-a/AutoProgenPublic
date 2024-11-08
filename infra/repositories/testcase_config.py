from contextlib import contextmanager
from typing import Iterable

from PyQt5.QtCore import QMutex

from domain.models.execute_config import TestCaseExecuteConfig
from domain.models.test_config import TestCaseTestConfig
from domain.models.testcase_config import TestCaseConfig
from domain.models.values import TestCaseID
from infra.io.files.current_project import CurrentProjectCoreIO
from infra.path_providers.current_project import TestCaseConfigPathProvider


class TestCaseConfigRepository:
    def __init__(
            self,
            *,
            testcase_config_path_provider: TestCaseConfigPathProvider,
            current_project_core_io: CurrentProjectCoreIO,
    ):
        self._testcase_config_path_provider = testcase_config_path_provider
        self._current_project_core_io = current_project_core_io

        self._lock = QMutex()
        self._testcase_cache: dict[TestCaseID, TestCaseConfig] = {}

    @contextmanager
    def __lock(self):
        self._lock.lock()
        try:
            yield
        finally:
            self._lock.unlock()

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
        try:
            if self.__read_execute_config(testcase_id) == execute_config:
                return
        except FileNotFoundError:
            pass
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
        try:
            if self.__read_test_config(testcase_id) == test_config:
                return
        except FileNotFoundError:
            pass
        self.__ensure_testcase_folder_exists(testcase_id)
        json_fullpath = self._testcase_config_path_provider.test_config_json_fullpath(
            testcase_id=testcase_id,
        )
        self._current_project_core_io.write_json(
            json_fullpath=json_fullpath,
            body=test_config.to_json(),
        )

    def put(self, testcase_config: TestCaseConfig):
        with self.__lock():
            if testcase_config.testcase_id in self._testcase_cache:
                del self._testcase_cache[testcase_config.testcase_id]

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

    def exists(self, testcase_id: TestCaseID) -> bool:
        with self.__lock():
            return any(
                str(testcase_id) in testcase_folder_name
                for testcase_folder_name in self.__iter_testcase_folder_names()
            )

    def get(self, testcase_id: TestCaseID) -> TestCaseConfig:
        with self.__lock():
            if testcase_id not in self._testcase_cache:
                execute_config = self.__read_execute_config(testcase_id=testcase_id)
                test_config = self.__read_test_config(testcase_id=testcase_id)
                self._testcase_cache[testcase_id] = TestCaseConfig(
                    testcase_id=testcase_id,
                    execute_config=execute_config,
                    test_config=test_config,
                )
            return self._testcase_cache[testcase_id]

    def list(self) -> list[TestCaseConfig]:
        return [
            self.get(TestCaseID(folder_name))
            for folder_name in sorted(self.__iter_testcase_folder_names())
        ]

    # def __delete_execute_config(self, testcase_id: TestCaseID) -> None:
    #     json_fullpath = self._testcase_config_path_provider.execute_config_json_fullpath(
    #         testcase_id=testcase_id,
    #     )
    #     if not json_fullpath.exists():
    #         raise FileNotFoundError("Execute config file does not exist")
    #     self._current_project_core_io.unlink(
    #         path=json_fullpath,
    #     )
    #
    # def __delete_test_config(self, testcase_id: TestCaseID) -> None:
    #     json_fullpath = self._testcase_config_path_provider.test_config_json_fullpath(
    #         testcase_id=testcase_id,
    #     )
    #     if not json_fullpath.exists():
    #         raise FileNotFoundError("Test config file does not exist")
    #     self._current_project_core_io.unlink(
    #         path=json_fullpath,
    #     )

    def delete(self, testcase_id: TestCaseID) -> None:
        with self.__lock():
            del self._testcase_cache[testcase_id]

            base_folder_fullpath = self._testcase_config_path_provider.testcase_folder_fullpath(
                testcase_id=testcase_id,
            )
            if not base_folder_fullpath.exists():
                raise FileNotFoundError("Test case does not exist")
            self._current_project_core_io.rmtree_folder(
                path=base_folder_fullpath,
            )
