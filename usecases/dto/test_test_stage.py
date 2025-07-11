from dataclasses import dataclass
from datetime import timedelta

from domain.models.test_result_output_file_entry import AbstractTestResultOutputFileEntry


@dataclass(slots=True)
class TestTestStageResult:
    regex_pattern: str | None  # None if error
    error_message: str | None  # None if success
    file_test_result: AbstractTestResultOutputFileEntry | None  # None if error
    test_execution_timedelta: timedelta | None  # None if error

    @property
    def has_error(self) -> bool:
        return self.error_message is not None

    @classmethod
    def create_error(
            cls,
            *,
            error_message: str,
    ):
        return cls(
            regex_pattern=None,
            error_message=error_message,
            file_test_result=None,
            test_execution_timedelta=None,
        )

    @classmethod
    def create_success(
            cls,
            *,
            regex_pattern: str,
            file_test_result: AbstractTestResultOutputFileEntry,
            test_execution_timedelta: timedelta,
    ):
        return cls(
            regex_pattern=regex_pattern,
            error_message=None,
            file_test_result=file_test_result,
            test_execution_timedelta=test_execution_timedelta,
        )
