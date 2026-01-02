from shared.domain.value.execute_config import TestCaseExecuteConfig
from shared.domain.value.identifier import TestCaseID
from shared.domain.value.test_config import TestCaseTestConfig


class TestCaseConfigEntity:
    def __init__(
            self,
            *,
            testcase_id: TestCaseID,
            execute_config: TestCaseExecuteConfig,
            test_config: TestCaseTestConfig,
    ):
        self._testcase_id = testcase_id  # IDフィールド: immutable
        self.execute_config = execute_config
        self.test_config = test_config

        self._validate()

    def _validate(self):
        if not isinstance(self._testcase_id, TestCaseID):
            raise TypeError(
                f"Expected 'testcase_id' to be TestCaseID, "
                f"got {type(self._testcase_id).__name__}: {self._testcase_id!r}"
            )
        if not isinstance(self.execute_config, TestCaseExecuteConfig):
            raise TypeError(
                f"Expected 'execute_config' to be TestCaseExecuteConfig, "
                f"got {type(self.execute_config).__name__}: {self.execute_config!r}"
            )
        if not isinstance(self.test_config, TestCaseTestConfig):
            raise TypeError(
                f"Expected 'test_config' to be TestCaseTestConfig, "
                f"got {type(self.test_config).__name__}: {self.test_config!r}"
            )

    @property
    def testcase_id(self) -> TestCaseID:
        """IDフィールド: Getterのみ（変更不可）"""
        return self._testcase_id

    def __eq__(self, other):
        """IDベースの等価性判定"""
        if not isinstance(other, TestCaseConfigEntity):
            return False
        return self._testcase_id == other._testcase_id

    def __hash__(self):
        """IDベースのハッシュ"""
        return hash(self._testcase_id)

    def to_json(self):
        return dict(
            testcase_id=self._testcase_id.to_json(),
            execute_config=self.execute_config.to_json(),
            test_config=self.test_config.to_json(),
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            testcase_id=TestCaseID.from_json(body["testcase_id"]),
            execute_config=TestCaseExecuteConfig.from_json(body["execute_config"]),
            test_config=TestCaseTestConfig.from_json(body["test_config"]),
        )
