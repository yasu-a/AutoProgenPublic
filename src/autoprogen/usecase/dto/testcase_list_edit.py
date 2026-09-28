from dataclasses import dataclass

from autoprogen.domain.model.value import TestCaseID


@dataclass(frozen=True)
class TestCaseListEditTestCaseSummary:
    testcase_id: TestCaseID
    name: str
    has_stdin: bool
    num_normal_files: int
