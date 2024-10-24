from dataclasses import dataclass

from domain.models.execute_config import TestCaseExecuteConfig
from domain.models.test_config import TestCaseTestConfig
from domain.models.values import TestCaseID


@dataclass(slots=True)
class TestCaseConfig:
    testcase_id: TestCaseID
    execute_config: TestCaseExecuteConfig
    test_config: TestCaseTestConfig
