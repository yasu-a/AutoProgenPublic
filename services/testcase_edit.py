import itertools
from dataclasses import dataclass

from domain.models.testcase import TestCaseConfig
from domain.models.values import TestCaseID
from files.testcase import TestCaseIO


@dataclass(frozen=True)
class TestCaseSummary:
    id: TestCaseID
    name: str
    has_stdin: bool
    num_normal_files: int


class TestCaseEditService:
    def __init__(
            self,
            testcase_io: TestCaseIO,
    ):
        self._testcase_io = testcase_io

    def list_testcase_ids(self) -> list[TestCaseID]:
        return self._testcase_io.list_ids()

    def get_summary(self, testcase_id: TestCaseID) -> TestCaseSummary:
        config = self._testcase_io.read_config(testcase_id)
        return TestCaseSummary(
            id=testcase_id,
            name=str(testcase_id),
            has_stdin=config.execute_config.has_stdin(),
            num_normal_files=config.execute_config.count_normal_files(),
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

    def create(self, testcase_id: TestCaseID) -> None:
        self._testcase_io.create_config(testcase_id)

    def delete(self, testcase_id: TestCaseID) -> None:
        self._testcase_io.delete_config(testcase_id)
