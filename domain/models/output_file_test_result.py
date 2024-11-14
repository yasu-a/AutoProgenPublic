from dataclasses import dataclass

from domain.models.pattern import AbstractPattern


@dataclass(slots=True)
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


@dataclass(slots=True)
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


@dataclass(slots=True)
class OutputFileTestResult:
    matched_tokens: list[MatchedToken]
    nonmatched_tokens: list[NonmatchedToken]

    @property
    def _are_all_matched_tokens_expected(self) -> bool:
        return all(
            matched_token.pattern.is_expected
            for matched_token in self.matched_tokens
        )

    @property
    def _are_all_nonmatched_tokens_unexpected(self) -> bool:
        return all(
            not nonmatched_token.pattern.is_expected
            for nonmatched_token in self.nonmatched_tokens
        )

    @property
    def is_accepted(self) -> bool:  # 正解かどうか
        return self._are_all_matched_tokens_expected and self._are_all_nonmatched_tokens_unexpected

    def to_json(self):
        return dict(
            matched_tokens=[token.to_json() for token in self.matched_tokens],
            nonmatched_tokens=[token.to_json() for token in self.nonmatched_tokens],
        )

    @classmethod
    def from_json(cls, body: dict):
        return cls(
            matched_tokens=[
                MatchedToken.from_json(token)
                for token in body["matched_tokens"]
            ],
            nonmatched_tokens=[
                NonmatchedToken.from_json(token)
                for token in body["nonmatched_tokens"]
            ],
        )
