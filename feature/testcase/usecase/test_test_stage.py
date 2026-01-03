from feature.testcase.usecase.interface import ITestTestStageUseCase
from feature.testcase.usecase.interface import TestTestStageResultDto
from shared.domain.error import MatchServiceError
from shared.domain.service.match import MatchGetBestService
from shared.domain.value.expected_output_file import ExpectedOutputFile
from shared.domain.value.output_file import OutputFile
from shared.domain.value.test_config_options import TestConfigOptions
from shared.domain.value.test_result_output_file_entry import TestResultTestedOutputFileEntry


class TestTestStageUseCase(ITestTestStageUseCase):
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
    ) -> TestTestStageResultDto:
        try:
            match_result = self._match_get_best_service.execute(
                content_string=content_text,
                test_config_options=test_config_options,
                patterns=expected_output_file.patterns,
            )
        except MatchServiceError as e:
            return TestTestStageResultDto.create_error(
                error_message=e.reason,
            )
        file_test_result = TestResultTestedOutputFileEntry(
            file_id=expected_output_file.file_id,
            actual=OutputFile(
                file_id=expected_output_file.file_id,
                content=content_text,
            ),
            expected=expected_output_file,
            test_result=match_result,
        )
        return TestTestStageResultDto.create_success(
            regex_pattern=match_result.regex_pattern,
            file_test_result=file_test_result,
            test_execution_timedelta=match_result.test_execution_timedelta,
        )
