from domain.models.expected_ouput_file import ExpectedOutputFile
from domain.models.output_file import OutputFile
from domain.models.output_file_test_result import OutputFileTestResult
from domain.models.test_config_options import TestConfigOptions
from domain.models.test_result_output_file_entry import TestResultTestedOutputFileEntry, \
    AbstractTestResultOutputFileEntry
from services.match import MatchGetBestService


class TestTestStageUseCase:
    def __init__(
            self,
            *,
            match_get_best_service: MatchGetBestService,
    ):
        self._match_get_best_service = match_get_best_service

    def execute(
            self,
            *,
            expected_output_file: ExpectedOutputFile,
            test_config_options: TestConfigOptions,
            content_text: str,
    ) -> AbstractTestResultOutputFileEntry:
        match_service_result = self._match_get_best_service.execute(
            content_string=content_text,
            test_config_options=test_config_options,
            patterns=expected_output_file.patterns,
        )
        file_test_result = TestResultTestedOutputFileEntry(
            file_id=expected_output_file.file_id,
            actual=OutputFile(
                file_id=expected_output_file.file_id,
                content=content_text,
            ),
            expected=expected_output_file,
            test_result=OutputFileTestResult(
                matched_tokens=match_service_result.matched_tokens,
                nonmatched_tokens=match_service_result.nonmatched_tokens,
            ),
        )
        return file_test_result
