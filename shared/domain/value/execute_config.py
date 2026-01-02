from dataclasses import dataclass
from datetime import datetime

from shared.domain.value.execute_config_options import ExecuteConfigOptions
from shared.domain.value.input_file import InputFileCollection


@dataclass(frozen=True)
class TestCaseExecuteConfig:
    # テストケースの構成のうち、実行に関する構成

    input_file_collection: InputFileCollection
    options: ExecuteConfigOptions
    mtime: datetime

    def to_json(self):
        return dict(
            input_file_collection=self.input_file_collection.to_json(),
            options=self.options.to_json(),
            mtime=self.mtime.isoformat(),
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            input_file_collection=InputFileCollection.from_json(
                body["input_file_collection"]),
            options=ExecuteConfigOptions.from_json(body["options"]),
            mtime=datetime.fromisoformat(body["mtime"]),
        )

    def __hash__(self) -> int:
        return hash((self.input_file_collection, self.options))

    def __eq__(self, other):
        if other is None:
            return False
        assert isinstance(other, type(self))
        return (
                self.input_file_collection == other.input_file_collection
                and self.options == other.options
        )
