import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cache
from typing import NamedTuple

from utils.zen_han import zen_to_han


class MatchRange(NamedTuple):
    begin: int
    end: int

    @classmethod
    def from_regex_match(cls, m: re.Match) -> "MatchRange":
        return cls(begin=m.start(), end=m.end())

    @property
    def length(self) -> int:
        return self.end - self.begin

    def __repr__(self):
        return f"MatchRange({self.begin}, {self.end})"


class MatchSource:
    # パターンマッチにかける対象となる文字列
    # パターンマッチに必要な正規表現マッチ結果を返し，場合に応じてキャッシュを提供する

    def __init__(self, source_text: str):
        self._source_text = source_text

    @property
    def source(self) -> str:
        return self._source_text

    @cache
    def list_regex_float_matches(self) -> tuple[re.Match, ...]:
        return tuple(
            re.finditer(
                r"\b[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?\b",
                self._source_text,
            )
        )

    @cache
    def list_space_or_eol_matches(self) -> tuple[re.Match, ...]:
        return tuple(
            re.finditer(
                r"\s*$\s*|\s+",
                self._source_text,
            )
        )

    @staticmethod
    def _create_regex_from_query_text(query_text: str) -> str:
        query_text = zen_to_han(query_text)
        words = re.findall(r"\S+", query_text)

        return r"\s+".join(re.escape(word) for word in words)

    @cache
    def list_regex_text_matches(self, pattern_text: str) -> tuple[re.Match, ...]:
        return tuple(
            re.finditer(
                self._create_regex_from_query_text(pattern_text),
                self._source_text,
                re.MULTILINE,
            )
        )


@dataclass(frozen=True)
class PatternMatchOptions:
    float_tolerance: float


@dataclass(frozen=True)
class AbstractPattern(ABC):
    # 出力ストリームの内容に期待されるトークンのパターン

    index: int  # パターンリスト内の位置
    is_expected: bool  # このパターンが出力に出現するor出現しない

    @classmethod
    def create_default(cls, index: int) -> "AbstractPattern":
        raise NotImplementedError()

    @abstractmethod
    def _fields_to_json(self) -> dict:
        return dict(
            index=self.index,
            is_expected=self.is_expected,
        )

    @classmethod
    @abstractmethod
    def _json_to_fields(cls, body: dict):
        return dict(
            index=body.pop("index"),
            is_expected=body.pop("is_expected"),
        )

    def to_json(self) -> dict:
        return dict(
            **self._fields_to_json(),
            type=type(self).__name__,
        )

    @classmethod
    def from_json(cls, body: dict):
        sub_classes = cls.__subclasses__()
        for sub_cls in sub_classes:
            sub_cls: type[AbstractPattern]
            if sub_cls.__name__ == body["type"]:
                # noinspection PyArgumentList
                return sub_cls(**sub_cls._json_to_fields(body))
        assert False, body

    @abstractmethod
    def find_matches(self, source: MatchSource, options: PatternMatchOptions) \
            -> list[MatchRange]:
        raise NotImplementedError()


@dataclass(frozen=True)
class TextPattern(AbstractPattern):
    text: str

    def __post_init__(self):
        assert isinstance(self.text, str), self.text

    def _fields_to_json(self) -> dict:
        return dict(
            **super()._fields_to_json(),
            text=self.text,
        )

    @classmethod
    def _json_to_fields(cls, body: dict):
        return dict(
            text=body.pop("text"),
            **super()._json_to_fields(body),
        )

    def __repr__(self):
        if self.is_expected:
            return f"s({self.text!r})"
        else:
            return f"s!({self.text!r})"

    @classmethod
    def create_default(cls, index: int) -> "TextPattern":
        return cls(index=index, is_expected=True, text="")

    # noinspection PyMethodOverriding
    def find_matches(self, source: MatchSource, options: PatternMatchOptions) \
            -> list[MatchRange]:
        return [
            MatchRange.from_regex_match(m)
            for m in source.list_regex_text_matches(pattern_text=self.text)
        ]


@dataclass(frozen=True)
class FloatPattern(AbstractPattern):
    value: int | float

    def __post_init__(self):
        assert isinstance(self.value, (int, float)), self.value

    def _fields_to_json(self) -> dict:
        return dict(
            **super()._fields_to_json(),
            value=self.value,
        )

    @classmethod
    def _json_to_fields(cls, body: dict):
        return dict(
            value=body.pop("value"),
            **super()._json_to_fields(body),
        )

    def __repr__(self):
        if self.is_expected:
            return f"f({self.value})"
        else:
            return f"f!({self.value})"

    @classmethod
    def create_default(cls, index: int) -> "FloatPattern":
        return cls(index=index, is_expected=True, value=0.0)

    # noinspection PyMethodOverriding
    def find_matches(self, source: MatchSource, options: PatternMatchOptions) \
            -> list[MatchRange]:
        return [
            MatchRange.from_regex_match(m)
            for m in source.list_regex_float_matches()
            if abs(float(m.group(0)) - self.value) <= options.float_tolerance
        ]


@dataclass(frozen=True)
class SpaceOrEOLPattern(AbstractPattern):
    def _fields_to_json(self) -> dict:
        return dict(
            **super()._fields_to_json(),
        )

    @classmethod
    def _json_to_fields(cls, body: dict):
        return dict(
            **super()._json_to_fields(body),
        )

    def __repr__(self):
        if self.is_expected:
            return f"space_or_eol()"
        else:
            return f"space_or_eol!()"

    @classmethod
    def create_default(cls, index: int) -> "SpaceOrEOLPattern":
        return cls(index=index, is_expected=True)

    # noinspection PyMethodOverriding
    def find_matches(self, source: MatchSource, options: PatternMatchOptions) \
            -> list[MatchRange]:
        return [
            MatchRange.from_regex_match(m)
            for m in source.list_space_or_eol_matches()
        ]


class PatternList(list[AbstractPattern]):
    def to_json(self) -> list:
        assert all(i == pattern.index for i, pattern in enumerate(self))
        return [
            pattern.to_json()
            for pattern in self
        ]

    @classmethod
    def from_json(cls, body: list):
        obj = cls([
            AbstractPattern.from_json(pattern_body)
            for pattern_body in body
        ])
        assert all(i == pattern.index for i, pattern in enumerate(obj))
        return obj

    def __hash__(self) -> int:
        return hash(tuple(self))

    def is_empty(self) -> bool:
        return len(self) == 0
