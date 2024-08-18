from domain.models.testcase import TestCaseExecuteConfig
from domain.models.values import TestCaseID


class TestCaseExecuteConfigHashMapping(dict[TestCaseID, int]):
    # テストケース全体から実行構成のハッシュのみを取り出したマッピングに対してハッシュを計算するための共通インターフェース

    def calculate_hash(self) -> int:
        return hash(tuple(sorted(self.items(), key=lambda x: x[0])))


class TestCaseExecuteConfigMapping(dict[TestCaseID, TestCaseExecuteConfig]):
    # テストケース全体から実行構成のみを取り出したマッピングに対してハッシュを計算するための共通インターフェース

    def to_testcase_execute_config_hash_mapping(self) -> TestCaseExecuteConfigHashMapping:
        return TestCaseExecuteConfigHashMapping({
            testcase_id: hash(testcase_execute_config)
            for testcase_id, testcase_execute_config in self.items()
        })

    def calculate_hash(self) -> int:
        return self.to_testcase_execute_config_hash_mapping().calculate_hash()
