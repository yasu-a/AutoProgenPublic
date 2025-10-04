from datetime import datetime

from domain.model.expected_output_file import ExpectedOutputFileCollection
from domain.model.test_config_options import TestConfigOptions


class TestCaseTestConfig:
    # テストケースの構成のうち、テストに関する構成

    def __init__(
            self,
            *,
            expected_output_file_collection: ExpectedOutputFileCollection,
            options: TestConfigOptions,
            mtime: datetime = None,
    ):
        self._expected_output_file_collection = expected_output_file_collection
        self._options = options
        self._mtime = mtime or datetime.now().isoformat()

    @property
    def expected_output_file_collection(self) -> ExpectedOutputFileCollection:
        return self._expected_output_file_collection

    @property
    def options(self):
        return self._options

    @property
    def mtime(self) -> datetime:
        return self._mtime

    def to_json(self):
        return dict(
            expected_output_file_collection=self._expected_output_file_collection.to_json(),
            options=self._options.to_json(),
            mtime=datetime.now().isoformat(),
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
                self._expected_output_file_collection == other._expected_output_file_collection
                and self._options == other._options
        )
