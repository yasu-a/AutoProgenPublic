from dataclasses import dataclass


@dataclass(slots=True)
class MatchedToken:
    match_begin: int
    match_end: int
    expected_token_index: int

    def to_json(self) -> dict:
        return dict(
            match_begin=self.match_begin,
            match_end=self.match_end,
            expected_token_index=self.expected_token_index,
        )

    @classmethod
    def from_json(cls, body: dict) -> "MatchedToken":
        return cls(
            match_begin=body["match_begin"],
            match_end=body["match_end"],
            expected_token_index=body["expected_token_index"],
        )


@dataclass(slots=True)
class NonmatchedToken:
    expected_token_index: int

    def to_json(self) -> dict:
        return dict(
            expected_token_index=self.expected_token_index,
        )

    @classmethod
    def from_json(cls, body: dict) -> "NonmatchedToken":
        return cls(
            expected_token_index=body["expected_token_index"],
        )


@dataclass(slots=True)
class OutputFileTestResult:
    matched_tokens: list[MatchedToken]
    nonmatched_tokens: list[NonmatchedToken]

    @property
    def is_accepted(self) -> bool:  # 正解かどうか
        return len(self.nonmatched_tokens) == 0

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
