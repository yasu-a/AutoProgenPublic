from dataclasses import dataclass

from domain.models.output_file_test_result import MatchedToken, NonmatchedToken


@dataclass(slots=True)
class MatchServiceResult:
    matched_tokens: list[MatchedToken]
    nonmatched_tokens: list[NonmatchedToken]
