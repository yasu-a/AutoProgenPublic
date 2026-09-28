from dataclasses import dataclass

from autoprogen.domain.model.execute_config import TestCaseExecuteConfig
from autoprogen.domain.model.test_config import TestCaseTestConfig
from autoprogen.domain.model.value import TestCaseID


@dataclass(slots=True)
class TestCaseConfig:
    testcase_id: TestCaseID
    execute_config: TestCaseExecuteConfig
    test_config: TestCaseTestConfig
