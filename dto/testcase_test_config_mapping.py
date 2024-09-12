from domain.models.testcase import TestCaseTestConfig
from domain.models.values import TestCaseID


class TestCaseTestConfigHashMapping(dict[TestCaseID, int]):
    # テストケース全体からテスト構成のハッシュのみを取り出したマッピングに対してハッシュを計算するための共通インターフェース

    def calculate_hash(self) -> int:
        return hash(tuple(sorted(self.items(), key=lambda x: x[0])))


class TestCaseTestConfigMapping(dict[TestCaseID, TestCaseTestConfig]):
    # テストケース全体からテスト構成のみを取り出したマッピングに対してハッシュを計算するための共通インターフェース

    def to_testcase_test_config_hash_mapping(self) -> TestCaseTestConfigHashMapping:
        return TestCaseTestConfigHashMapping({
            testcase_id: hash(testcase_execute_config)
            for testcase_id, testcase_execute_config in self.items()
        })

    def calculate_hash(self) -> int:
        return self.to_testcase_test_config_hash_mapping().calculate_hash()
