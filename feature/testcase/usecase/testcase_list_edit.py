import itertools

from feature.testcase.usecase.dto import TestCaseSummary
from feature.testcase.usecase.interface import (
    ITestCaseListSummaryUseCase,
    ITestCaseCreateNewNameUseCase,
    ITestCaseCreateUseCase,
    ITestCaseCopyUseCase,
)
from shared.domain.value.execute_config_options import ExecuteConfigOptions
from shared.domain.value.input_file import InputFileCollection
from shared.domain.error import UseCaseError, ServiceError
from shared.domain.entity.testcase_config import TestCaseConfigEntity
from shared.domain.interface.gateway import ICurrentDatetimeGateway
from shared.domain.interface.service import (
    ITestCaseConfigCopyService,
)
from shared.domain.value.execute_config import TestCaseExecuteConfig
from shared.domain.value.expected_output_file import ExpectedOutputFileCollection
from shared.domain.value.identifier import TestCaseID
from shared.domain.value.test_config import TestCaseTestConfig
from shared.domain.value.test_config_options import TestConfigOptions
from shared.infra.repository.testcase_config import TestCaseConfigRepository


class TestCaseListSummaryUseCase(ITestCaseListSummaryUseCase):
    # テストケース構成の要約をリストアップする
    def __init__(
            self,
            testcase_config_repo: TestCaseConfigRepository,
    ):
        self._testcase_config_repo = testcase_config_repo

    def execute(self) -> list[TestCaseSummary]:
        return [
            TestCaseSummary(
                testcase_id=testcase_config.testcase_id,
                name=str(testcase_config.testcase_id),
                has_stdin=testcase_config.execute_config.input_file_collection.has_stdin,
                num_normal_files=testcase_config.execute_config.input_file_collection.normal_file_count,
            )
            for testcase_config in self._testcase_config_repo.list()
        ]


class TestCaseCreateNewNameUseCase(ITestCaseCreateNewNameUseCase):
    # 既存のテストケース名と衝突しない新しいテストケース名を生成する

    def __init__(
            self,
            *,
            testcase_config_repo: TestCaseConfigRepository,
    ):
        self._testcase_config_repo = testcase_config_repo

    def execute(self) -> str:
        new_testcase_id_format = "テストケース{number:02d}"
        testcase_id_set = {
            testcase_config.testcase_id
            for testcase_config in self._testcase_config_repo.list()
        }
        for i in itertools.count():
            new_testcase_id = TestCaseID(new_testcase_id_format.format(number=i + 1))
            if new_testcase_id not in testcase_id_set:
                return str(new_testcase_id)
        assert False, "unreachable"


class TestCaseCreateUseCase(ITestCaseCreateUseCase):
    # 新しいテストケースを生成する

    def __init__(
            self,
            *,
            testcase_config_repo: TestCaseConfigRepository,
            current_datetime_gateway: ICurrentDatetimeGateway,
    ):
        self._testcase_config_repo = testcase_config_repo
        self._current_datetime_gateway = current_datetime_gateway

    def execute(self, testcase_name: str) -> None:
        current_datetime = self._current_datetime_gateway.execute()
        config = TestCaseConfigEntity(
            testcase_id=TestCaseID(testcase_name),
            execute_config=TestCaseExecuteConfig(
                input_file_collection=InputFileCollection(),
                options=ExecuteConfigOptions(
                    timeout=5.0,
                ),
                mtime=current_datetime,
            ),
            test_config=TestCaseTestConfig(
                expected_output_file_collection=ExpectedOutputFileCollection(),
                options=TestConfigOptions(
                    ignore_case=True,
                ),
                mtime=current_datetime,
            ),
        )

        if self._testcase_config_repo.exists(config.testcase_id):
            raise UseCaseError("testcase already exists")
        self._testcase_config_repo.put(config)


class TestCaseCopyUseCase(ITestCaseCopyUseCase):
    # テストケースのコピーを作成する

    def __init__(
            self,
            *,
            testcase_config_copy_service: ITestCaseConfigCopyService,
    ):
        self._testcase_config_copy_service = testcase_config_copy_service

    def execute(self, *, src_testcase_id: TestCaseID, new_testcase_name: str) -> None:
        new_testcase_id = TestCaseID(new_testcase_name)
        try:
            self._testcase_config_copy_service.execute(src_testcase_id, new_testcase_id)
        except ServiceError:
            raise UseCaseError("testcase already exists")
