import itertools

from domain.errors import UseCaseError, ServiceError
from domain.models.execute_config import TestCaseExecuteConfig
from domain.models.execute_config_options import ExecuteConfigOptions
from domain.models.expected_output_file import ExpectedOutputFileMapping
from domain.models.input_file import InputFileMapping
from domain.models.test_config import TestCaseTestConfig
from domain.models.test_config_options import TestConfigOptions
from domain.models.testcase_config import TestCaseConfig
from domain.models.values import TestCaseID
from infra.repositories.testcase_config import TestCaseConfigRepository
from services.testcase_config import TestCaseConfigListIDSubService, TestCaseConfigCopyService
from usecases.dto.testcase_list_edit import TestCaseListEditTestCaseSummary


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
                has_stdin=testcase_config.execute_config.input_files.has_stdin,
                num_normal_files=testcase_config.execute_config.input_files.normal_file_count,
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
                input_files=InputFileMapping(),
                options=ExecuteConfigOptions(
                    timeout=5.0,
                ),
            ),
            test_config=TestCaseTestConfig(
                expected_output_files=ExpectedOutputFileMapping(),
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
