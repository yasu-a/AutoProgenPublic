import copy
import re
from datetime import datetime

from domain.models.output_file_test_result import NonmatchedToken, MatchedToken
from domain.models.pattern import PatternList
from domain.models.test_config_options import TestConfigOptions
from services.dto.match_result import MatchServiceResult
from utils.app_logging import create_logger
from utils.zen_han import zen_to_han


class _Matcher:
    _logger = create_logger()

    def __init__(
            self,
            *,
            content_string: str,
            patterns: PatternList,
            test_config_options: TestConfigOptions,
    ):
        self._content_string = zen_to_han(content_string)
        self._patterns = copy.deepcopy(patterns)
        self._test_config_options = test_config_options

    def get_best_token_matches(self) -> tuple[str, list[MatchedToken], list[NonmatchedToken]]:
        regex_pattern, flags = self._patterns.to_regex_pattern(
            ignore_case=self._test_config_options.ignore_case,
        )

        match_result = re.fullmatch(regex_pattern, self._content_string, flags=flags)

        matched_tokens: list[MatchedToken] = []
        nonmatched_tokens: list[NonmatchedToken] = []
        if match_result is None:
            for pattern in self._patterns:
                nonmatched_tokens.append(
                    NonmatchedToken(
                        pattern=pattern,
                    )
                )
        else:
            group_dict = match_result.groupdict()
            for pattern in self._patterns:
                is_found = group_dict[pattern.regex_group_name]
                if is_found:
                    matched_tokens.append(
                        MatchedToken(
                            begin=match_result.start(pattern.regex_group_name),
                            end=match_result.end(pattern.regex_group_name),
                            pattern=pattern,
                        )
                    )
                else:
                    nonmatched_tokens.append(
                        NonmatchedToken(
                            pattern=pattern,
                        )
                    )

        return regex_pattern, matched_tokens, nonmatched_tokens


class MatchGetBestService:
    _logger = create_logger()

    def __init__(self):
        pass

    @classmethod
    def execute(
            cls,
            *,
            content_string: str,
            patterns: PatternList,
            test_config_options: TestConfigOptions,
    ) -> MatchServiceResult:
        # マッチングを実行
        matcher = _Matcher(
            content_string=content_string,
            patterns=patterns,
            test_config_options=test_config_options,
        )
        time_start = datetime.now()
        regex_pattern, matched_tokens, nonmatched_tokens = matcher.get_best_token_matches()
        time_end = datetime.now()

        # 結果を生成
        return MatchServiceResult(
            regex_pattern=regex_pattern,
            matched_tokens=matched_tokens,
            nonmatched_tokens=nonmatched_tokens,
            test_execution_timedelta=time_end - time_start,
        )
