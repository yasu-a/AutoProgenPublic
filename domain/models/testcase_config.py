from dataclasses import dataclass

from domain.models.execute_config import TestCaseExecuteConfig
from domain.models.test_config import TestCaseTestConfig


@dataclass(slots=True)
class TestCaseConfig:
    execute_config: TestCaseExecuteConfig
    test_config: TestCaseTestConfig
