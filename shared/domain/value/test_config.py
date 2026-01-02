from dataclasses import dataclass
from datetime import datetime

from shared.domain.value.expected_output_file import ExpectedOutputFileCollection
from shared.domain.value.test_config_options import TestConfigOptions


@dataclass(frozen=True)
class TestCaseTestConfig:
    # テストケースの構成のうち、テストに関する構成

    expected_output_file_collection: ExpectedOutputFileCollection
    options: TestConfigOptions
    mtime: datetime

    def to_json(self):
        return dict(
            expected_output_file_collection=self.expected_output_file_collection.to_json(),
            options=self.options.to_json(),
            mtime=self.mtime.isoformat(),
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            expected_output_file_collection=ExpectedOutputFileCollection.from_json(
                body['expected_output_file_collection']
            ),
            options=TestConfigOptions.from_json(body['options']),
            mtime=datetime.fromisoformat(body["mtime"]),
        )

    def __eq__(self, other):
        if other is None:
            return False
        assert isinstance(other, type(self))
        return (
                self.expected_output_file_collection == other.expected_output_file_collection
                and self.options == other.options
        )
