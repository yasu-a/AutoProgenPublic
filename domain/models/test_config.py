from domain.models.expected_ouput_file import ExpectedOutputFileMapping
from domain.models.test_config_options import TestConfigOptions


class TestCaseTestConfig:
    def __init__(
            self,
            *,
            expected_output_files: ExpectedOutputFileMapping,
            options: TestConfigOptions,
    ):
        self._expected_output_files = expected_output_files
        self._options = options

    @property
    def expected_output_files(self):
        return self._expected_output_files

    @property
    def options(self):
        return self._options

    def to_json(self):
        return dict(
            expected_output_files=self._expected_output_files.to_json(),
            options=self._options.to_json(),
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            expected_output_files=ExpectedOutputFileMapping.from_json(
                body['expected_output_files']
            ),
            options=TestConfigOptions.from_json(body['options']),
        )

    def __hash__(self) -> int:
        return hash((self._expected_output_files, self._options))
