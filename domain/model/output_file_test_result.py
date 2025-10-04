from dataclasses import dataclass
from datetime import timedelta
from typing import Iterable

from domain.model.pattern import AbstractPattern


@dataclass(frozen=True)
class MatchedToken:
    pattern: AbstractPattern
    begin: int
    end: int

    def to_json(self) -> dict:
        return dict(
            pattern=self.pattern.to_json(),
            begin=self.begin,
            end=self.end,
        )

    @classmethod
    def from_json(cls, body: dict) -> "MatchedToken":
        return cls(
            pattern=AbstractPattern.from_json(body["pattern"]),
            begin=body["begin"],
            end=body["end"],
        )

    def __repr__(self):
        return f"MatchedToken({self.pattern.index}, {self.begin}, {self.end})"


@dataclass(frozen=True)
class NonmatchedToken:
    pattern: AbstractPattern

    def to_json(self) -> dict:
        return dict(
            pattern=self.pattern.to_json(),
        )

    @classmethod
    def from_json(cls, body: dict) -> "NonmatchedToken":
        return cls(
            pattern=AbstractPattern.from_json(body["pattern"]),
        )

    def __repr__(self):
        return f"NonmatchedToken({self.pattern.index})"


class MatchResult:
    def __init__(
            self,
            *,
            regex_pattern: str,
            matched_tokens: Iterable[MatchedToken],
            nonmatched_tokens: Iterable[NonmatchedToken],
            test_execution_timedelta: timedelta,
    ):
        self._regex_pattern = regex_pattern
        self._matched_tokens = sorted(matched_tokens, key=lambda token: token.pattern.index)
        self._nonmatched_tokens = sorted(nonmatched_tokens, key=lambda token: token.pattern.index)
        self._test_execution_timedelta = test_execution_timedelta

    @property
    def regex_pattern(self) -> str:
        return self._regex_pattern

    @property
    def matched_tokens(self) -> list[MatchedToken]:
        return list(self._matched_tokens)

    @property
    def nonmatched_tokens(self) -> list[NonmatchedToken]:
        return list(self._nonmatched_tokens)

    @property
    def test_execution_timedelta(self) -> timedelta:
        return self._test_execution_timedelta

    @property
    def _are_all_matched_tokens_expected(self) -> bool:
        return all(
            matched_token.pattern.is_expected
            for matched_token in self._matched_tokens
        )

    @property
    def _are_all_nonmatched_tokens_unexpected(self) -> bool:
        return all(
            not nonmatched_token.pattern.is_expected
            for nonmatched_token in self._nonmatched_tokens
        )

    @property
    def is_accepted(self) -> bool:  # 正解かどうか
        return self._are_all_matched_tokens_expected and self._are_all_nonmatched_tokens_unexpected

    def to_json(self):
        return dict(
            regex_pattern=self._regex_pattern,
            matched_tokens=[token.to_json() for token in self._matched_tokens],
            nonmatched_tokens=[token.to_json() for token in self._nonmatched_tokens],
            test_execution_timedelta=self._test_execution_timedelta.total_seconds(),
        )

    def count_matched_tokens(self) -> int:
        return len(self._matched_tokens)

    def count_nonmatched_tokens(self) -> int:
        return len(self._nonmatched_tokens)

    @classmethod
    def from_json(cls, body: dict):
        return cls(
            regex_pattern=body["regex_pattern"],
            matched_tokens=[MatchedToken.from_json(token) for token in body["matched_tokens"]],
            nonmatched_tokens=[NonmatchedToken.from_json(token) for token in
                               body["nonmatched_tokens"]],
            test_execution_timedelta=timedelta(seconds=body["test_execution_timedelta"]),
        )