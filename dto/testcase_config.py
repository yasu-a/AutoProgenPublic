from domain.models.testcase_config import TestCaseConfig
from domain.models.values import TestCaseID


class TestCaseConfigMapping(dict[TestCaseID, TestCaseConfig]):
    pass
