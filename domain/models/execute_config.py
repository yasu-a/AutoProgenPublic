from datetime import datetime

from domain.models.execute_config_options import ExecuteConfigOptions
from domain.models.input_file import InputFileCollection


class TestCaseExecuteConfig:
    # テストケースの構成のうち、実行に関する構成

    def __init__(
            self,
            *,
            input_file_collection: InputFileCollection,
            options: ExecuteConfigOptions,
            mtime: datetime = None,
    ):
        self._input_file_collection = input_file_collection
        self._options = options
        self._mtime = mtime or datetime.now().isoformat()

    @property
    def input_file_collection(self) -> InputFileCollection:
        return self._input_file_collection

    @property
    def options(self) -> ExecuteConfigOptions:
        return self._options

    @property
    def mtime(self) -> datetime:
        return self._mtime

    def to_json(self):
        return dict(
            input_file_collection=self._input_file_collection.to_json(),
            options=self._options.to_json(),
            mtime=datetime.now().isoformat(),
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            input_file_collection=InputFileCollection.from_json(body["input_file_collection"]),
            options=ExecuteConfigOptions.from_json(body["options"]),
            mtime=datetime.fromisoformat(body["mtime"]),
        )

    def __hash__(self) -> int:
        return hash((self._input_file_collection, self._options))

    def __eq__(self, other):
        if other is None:
            return False
        assert isinstance(other, type(self))
        return (
                self._input_file_collection == other._input_file_collection
                and self._options == other._options
        )
