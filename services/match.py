import copy
import re
from datetime import datetime

from domain.models.output_file_test_result import NonmatchedToken, MatchedToken, MatchResult
from domain.models.pattern import PatternList
from domain.models.test_config_options import TestConfigOptions
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
        # 期待されるパターンと期待されないパターンを分離
        expected_patterns = self._patterns.expected_patterns

        matched_tokens: list[MatchedToken] = []
        nonmatched_tokens: list[NonmatchedToken] = []

        # 期待されるパターンのマッチング
        regex_pattern, flags = expected_patterns.to_regex_pattern(
            ignore_case=self._test_config_options.ignore_case,
        )
        expected_pattern_match_result \
            = re.fullmatch(regex_pattern, self._content_string, flags=flags)

        if expected_pattern_match_result is None:
            # 期待されるパターンがマッチしない場合
            for pattern in self._patterns:
                nonmatched_tokens.append(
                    NonmatchedToken(
                        pattern=pattern,
                    )
                )
            return regex_pattern, matched_tokens, nonmatched_tokens

        # 期待されるパターンがマッチした場合
        group_dict = expected_pattern_match_result.groupdict()
        spans: dict[int, tuple[int, int]] = {}  # pattern index -> span
        for pattern in expected_patterns:
            is_found = group_dict[pattern.regex_group_name]
            begin = expected_pattern_match_result.start(pattern.regex_group_name)
            end = expected_pattern_match_result.end(pattern.regex_group_name)
            spans[pattern.index] = begin, end
            if is_found:
                matched_tokens.append(
                    MatchedToken(
                        begin=begin,
                        end=end,
                        pattern=pattern,
                    )
                )
            else:
                nonmatched_tokens.append(
                    NonmatchedToken(
                        pattern=pattern,
                    )
                )

        # 期待されないパターンを順序付きでマッチング
        for unexpected_patterns in self._patterns.iter_unexpected_patterns():
            if unexpected_patterns.first_pattern_index == self._patterns.first_pattern_index:
                interval_begin = 0
            else:
                interval_begin = spans[unexpected_patterns.first_pattern_index - 1][1]

            if unexpected_patterns.last_pattern_index == self._patterns.last_pattern_index:
                interval_end = len(self._content_string)
            else:
                interval_end = spans[unexpected_patterns.last_pattern_index + 1][0]

            interval_text = self._content_string[interval_begin:interval_end]

            regex_pattern, flags = unexpected_patterns.to_regex_pattern(
                ignore_case=self._test_config_options.ignore_case,
            )
            unexpected_pattern_match_result \
                = re.search(regex_pattern, interval_text, flags=flags)
            if unexpected_pattern_match_result is None:
                for p in unexpected_patterns:
                    nonmatched_tokens.append(
                        NonmatchedToken(
                            pattern=p,
                        )
                    )
            else:
                for p in unexpected_patterns:
                    begin = unexpected_pattern_match_result.start(p.regex_group_name)
                    end = unexpected_pattern_match_result.end(p.regex_group_name)
                    matched_tokens.append(
                        MatchedToken(
                            begin=interval_begin + begin,
                            end=interval_begin + end,
                            pattern=p,
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
    ) -> MatchResult:
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
        return MatchResult(
            regex_pattern=regex_pattern,
            matched_tokens=matched_tokens,
            nonmatched_tokens=nonmatched_tokens,
            test_execution_timedelta=time_end - time_start,
        )
