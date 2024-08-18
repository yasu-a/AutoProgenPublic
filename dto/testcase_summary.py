from dataclasses import dataclass

from domain.models.values import TestCaseID


@dataclass(frozen=True)
class TestCaseEditTestCaseSummary:
    id: TestCaseID
    name: str
    has_stdin: bool
    num_normal_files: int
