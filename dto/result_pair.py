from dataclasses import dataclass

from domain.models.output_file import OutputFile
from domain.models.result_execute import TestCaseExecuteResult
from domain.models.result_test import OutputFileTestResult, TestCaseTestResult
from domain.models.values import FileID, TestCaseID


@dataclass(slots=True)
class OutputFileAndTestResultPair:
    file_id: FileID
    output_file: OutputFile
    test_result: OutputFileTestResult


@dataclass(slots=True)
class TestCaseExecuteAndTestResultPair:
    testcase_id: TestCaseID
    execute_result: TestCaseExecuteResult
    test_result: TestCaseTestResult

    def __post_init__(self):
        # TODO: データレベルで整合性を保証する

        # テストケースIDの整合性を確認
        assert self.execute_result.testcase_id == self.test_result.testcase_id, \
            (self.execute_result.testcase_id, self.test_result.testcase_id)
        assert self.test_result.testcase_id == self.test_result.testcase_id, \
            (self.test_result.testcase_id, self.test_result.testcase_id)
        # ファイルIDの整合性を確認
        assert (
                set(self.execute_result.output_files.keys())
                == set(self.test_result.output_file_test_results.keys())
        ), (
            set(self.execute_result.output_files.keys()),
            set(self.test_result.output_file_test_results),
        )

    def list_file_ids(self) -> list[FileID]:
        return sorted(self.execute_result.output_files.keys())

    def get_output_file_and_test_result_pair(self, file_id: FileID) -> OutputFileAndTestResultPair:
        output_file = self.execute_result.output_files.get(file_id)
        test_result_pair = self.test_result.output_file_test_results.get(file_id)
        if output_file is None or test_result_pair is None:
            raise KeyError(file_id)
        return OutputFileAndTestResultPair(file_id, output_file, test_result_pair)


class TestCaseExecuteAndTestResultPairMapping(dict[TestCaseID, TestCaseExecuteAndTestResultPair]):
    pass
