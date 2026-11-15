from dataclasses import dataclass

from autoprogen.domain.model.execute_config import TestCaseExecuteConfig
from autoprogen.domain.model.execute_config_options import ExecuteConfigOptions
from autoprogen.domain.model.expected_output_file import ExpectedOutputFileCollection
from autoprogen.domain.model.input_file import InputFileCollection
from autoprogen.domain.model.test_config import TestCaseTestConfig
from autoprogen.domain.model.test_config_options import TestConfigOptions
from autoprogen.domain.model.value import TestCaseID


@dataclass(slots=True)
class TestCaseConfig:
    """一つのテストケースで使用する実行設定と判定設定を保持する。"""

    # テストケースを一意に識別する名前。
    testcase_id: TestCaseID
    # プログラムへ与える入力と実行時の設定。
    execute_config: TestCaseExecuteConfig
    # 期待する出力と比較時の設定。
    test_config: TestCaseTestConfig

    @classmethod
    def create_default(cls, testcase_id: TestCaseID) -> "TestCaseConfig":
        """指定したIDを持つ既定のテストケース設定を生成する。"""
        return cls(
            testcase_id=testcase_id,
            execute_config=TestCaseExecuteConfig(
                input_file_collection=InputFileCollection(),
                options=ExecuteConfigOptions(timeout=5.0),
            ),
            test_config=TestCaseTestConfig(
                expected_output_file_collection=ExpectedOutputFileCollection(),
                options=TestConfigOptions(ignore_case=True),
            ),
        )
