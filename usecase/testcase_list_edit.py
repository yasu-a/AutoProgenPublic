import itertools

from domain.error import UseCaseError, ServiceError
from domain.model.execute_config import TestCaseExecuteConfig
from domain.model.execute_config_options import ExecuteConfigOptions
from domain.model.expected_output_file import ExpectedOutputFileCollection
from domain.model.input_file import InputFileCollection
from domain.model.test_config import TestCaseTestConfig
from domain.model.test_config_options import TestConfigOptions
from domain.model.testcase_config import TestCaseConfig
from domain.model.value import TestCaseID
from infra.repository.testcase_config import TestCaseConfigRepository
from service.testcase_config import TestCaseConfigListIDSubService, TestCaseConfigCopyService
from usecase.dto.testcase_list_edit import TestCaseListEditTestCaseSummary


class TestCaseListEditListSummaryUseCase:
    # テストケース構成の要約をリストアップする
    def __init__(
            self,
            testcase_config_repo: TestCaseConfigRepository,
    ):
        self._testcase_config_repo = testcase_config_repo

    def execute(self) -> list[TestCaseListEditTestCaseSummary]:
        return [
            TestCaseListEditTestCaseSummary(
                testcase_id=testcase_config.testcase_id,
                name=str(testcase_config.testcase_id),
                has_stdin=testcase_config.execute_config.input_file_collection.has_stdin,
                num_normal_files=testcase_config.execute_config.input_file_collection.normal_file_count,
            )
            for testcase_config in self._testcase_config_repo.list()
        ]


class TestCaseListEditCreateNewNameUseCase:
    # 既存のテストケース名と衝突しない新しいテストケース名を生成する

    def __init__(
            self,
            *,
            testcase_config_list_id_sub_service: TestCaseConfigListIDSubService,
    ):
        self._testcase_config_list_id_sub_service = testcase_config_list_id_sub_service

    def execute(self) -> str:
        new_testcase_id_format = "テストケース{number:02d}"
        testcase_id_set = set(self._testcase_config_list_id_sub_service.execute())
        for i in itertools.count():
            new_testcase_id = TestCaseID(new_testcase_id_format.format(number=i + 1))
            if new_testcase_id not in testcase_id_set:
                return str(new_testcase_id)
        assert False, "unreachable"


class TestCaseListEditCreateTestCaseUseCase:
    # 新しいテストケースを生成する

    def __init__(
            self,
            *,
            testcase_config_repo: TestCaseConfigRepository,
    ):
        self._testcase_config_repo = testcase_config_repo

    def execute(self, testcase_name: str) -> None:
        config = TestCaseConfig(
            testcase_id=TestCaseID(testcase_name),
            execute_config=TestCaseExecuteConfig(
                input_file_collection=InputFileCollection(),
                options=ExecuteConfigOptions(
                    timeout=5.0,
                ),
            ),
            test_config=TestCaseTestConfig(
                expected_output_file_collection=ExpectedOutputFileCollection(),
                options=TestConfigOptions(
                    ignore_case=True,
                ),
            ),
        )

        if self._testcase_config_repo.exists(config.testcase_id):
            raise UseCaseError("testcase already exists")
        self._testcase_config_repo.put(config)


class TestCaseListEditCopyTestCaseUseCase:
    # テストケースのコピーを作成する

    def __init__(
            self,
            *,
            testcase_config_copy_service: TestCaseConfigCopyService,
    ):
        self._testcase_config_copy_service = testcase_config_copy_service

    def execute(self, *, src_testcase_id: TestCaseID, new_testcase_name: str) -> None:
        new_testcase_id = TestCaseID(new_testcase_name)
        try:
            self._testcase_config_copy_service.execute(src_testcase_id, new_testcase_id)
        except ServiceError:
            raise UseCaseError("testcase already exists")
