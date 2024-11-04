from datetime import datetime

from domain.models.expected_ouput_file import ExpectedOutputFileMapping
from domain.models.test_config_options import TestConfigOptions


class TestCaseTestConfig:
    def __init__(
            self,
            *,
            expected_output_files: ExpectedOutputFileMapping,
            options: TestConfigOptions,
            mtime: datetime = None,
    ):
        self._expected_output_files = expected_output_files
        self._options = options
        self._mtime = mtime or datetime.now().isoformat()

    @property
    def expected_output_files(self) -> ExpectedOutputFileMapping:
        return self._expected_output_files

    @property
    def options(self):
        return self._options

    @property
    def mtime(self) -> datetime:
        return self._mtime

    def to_json(self):
        return dict(
            expected_output_files=self._expected_output_files.to_json(),
            options=self._options.to_json(),
            mtime=datetime.now().isoformat(),
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            expected_output_files=ExpectedOutputFileMapping.from_json(
                body['expected_output_files']
            ),
            options=TestConfigOptions.from_json(body['options']),
            mtime=datetime.fromisoformat(body["mtime"]),
        )

    def __hash__(self) -> int:
        return hash((self._expected_output_files, self._options))
