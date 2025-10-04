from dataclasses import dataclass

from domain.model.execute_config import TestCaseExecuteConfig
from domain.model.test_config import TestCaseTestConfig
from domain.model.value import TestCaseID


@dataclass(slots=True)
class TestCaseConfig:
    testcase_id: TestCaseID
    execute_config: TestCaseExecuteConfig
    test_config: TestCaseTestConfig
