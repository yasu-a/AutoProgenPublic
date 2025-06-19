from dataclasses import dataclass
from datetime import timedelta

from domain.models.output_file_test_result import MatchedToken, NonmatchedToken


@dataclass(slots=True)
class MatchServiceResult:
    regex_pattern: str
    matched_tokens: list[MatchedToken]
    nonmatched_tokens: list[NonmatchedToken]
    test_execution_timedelta: timedelta
