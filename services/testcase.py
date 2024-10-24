import itertools

from domain.models.execute_config import TestCaseExecuteConfig
from domain.models.execute_config_options import ExecuteConfigOptions
from domain.models.expected_ouput_file import ExpectedOutputFileMapping
from domain.models.input_file import InputFileMapping
from domain.models.test_config import TestCaseTestConfig
from domain.models.test_config_options import TestConfigOptions
from domain.models.testcase_config import TestCaseConfig
from domain.models.values import TestCaseID
from dto.testcase_summary import TestCaseEditTestCaseSummary
from files.repositories.testcase_config import TestCaseConfigRepository
from files.testcase_config import TestCaseIO


class TestCaseListIDSubService:
    def __init__(
            self,
            *,
            testcase_config_repo: TestCaseConfigRepository,
    ):
        self.testcase_config_repo = testcase_config_repo

    def execute(self) -> list[TestCaseID]:
        return [
            testcase_config.testcase_id
            for testcase_config in self.testcase_config_repo.list()
        ]


class TestCaseService:
    def __init__(
            self,
            testcase_io: TestCaseIO,
    ):
        self._testcase_io = testcase_io

    def list_testcase_ids(self) -> list[TestCaseID]:
        return self._testcase_io.list_ids()

    def get_summary(self, testcase_id: TestCaseID) -> TestCaseEditTestCaseSummary:
        config = self._testcase_io.read_config(testcase_id)
        return TestCaseEditTestCaseSummary(
            id=testcase_id,
            name=str(testcase_id),
            has_stdin=config.execute_config.input_files.has_stdin,
            num_normal_files=config.execute_config.input_files.normal_file_count,
        )

    def get_config(self, testcase_id: TestCaseID) -> TestCaseConfig:
        return self._testcase_io.read_config(testcase_id)

    def set_config(self, testcase_id: TestCaseID, config: TestCaseConfig):
        self._testcase_io.write_config(testcase_id, config)

    def create_new_testcase_id(self) -> TestCaseID:
        new_testcase_id_format = "テストケース{number:02d}"
        testcase_id_set = set(self._testcase_io.list_ids())
        for i in itertools.count():
            new_testcase_id = TestCaseID(new_testcase_id_format.format(number=i + 1))
            if new_testcase_id not in testcase_id_set:
                return new_testcase_id

    def create(self, testcase_id: TestCaseID) -> None:  # TODO: use-case に分離
        config = TestCaseConfig(
            execute_config=TestCaseExecuteConfig(
                input_files=InputFileMapping(),
                options=ExecuteConfigOptions(
                    timeout=5.0,
                ),
            ),
            test_config=TestCaseTestConfig(
                expected_output_files=ExpectedOutputFileMapping(),
                options=TestConfigOptions(
                    ordered_matching=True,
                    float_tolerance=1.0e-6,
                    allowable_edit_distance=0,
                    # ignore_whitespace=False,
                ),
            ),
        )
        self._testcase_io.create_config(testcase_id, config)

    def delete(self, testcase_id: TestCaseID) -> None:
        self._testcase_io.delete_config(testcase_id)
