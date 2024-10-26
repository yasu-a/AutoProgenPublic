from datetime import datetime

from domain.models.execute_config_options import ExecuteConfigOptions
from domain.models.input_file import InputFileMapping


class TestCaseExecuteConfig:
    def __init__(
            self,
            *,
            input_files: InputFileMapping,
            options: ExecuteConfigOptions,
            mtime: datetime = None,
    ):
        self._input_files = input_files
        self._options = options
        self._mtime = mtime or datetime.now().isoformat()

    @property
    def input_files(self) -> InputFileMapping:
        return self._input_files

    @property
    def options(self) -> ExecuteConfigOptions:
        return self._options

    @property
    def mtime(self) -> datetime:
        return self._mtime

    def to_json(self):
        return dict(
            input_files=self._input_files.to_json(),
            options=self._options.to_json(),
            mtime=datetime.now().isoformat(),
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            input_files=InputFileMapping.from_json(body["input_files"]),
            options=ExecuteConfigOptions.from_json(body["options"]),
            mtime=datetime.fromisoformat(body["mtime"]),
        )

    def __hash__(self) -> int:
        return hash((self._input_files, self._options))
