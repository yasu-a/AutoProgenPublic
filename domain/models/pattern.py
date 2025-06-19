import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import NamedTuple


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


@dataclass(frozen=True)
class PatternMatchOptions:
    float_tolerance: float


@dataclass(frozen=True)
class AbstractPattern(ABC):
    # 出力ストリームの内容に期待されるトークンのパターン

    index: int  # パターンリスト内の位置
    is_expected: bool  # このパターンが出力に出現するor出現しない

    @classmethod
    @abstractmethod
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
    def _to_regex(self) -> str:
        raise NotImplementedError()

    @property
    def regex_group_name(self) -> str:
        return f"_{self.index}"

    def to_regex_with_group(self):
        if self.is_expected:
            return "(?P<" + self.regex_group_name + ">" + self._to_regex() + ")"
        else:
            return "(?P<" + self.regex_group_name + ">" + self._to_regex() + ")?"


@dataclass(frozen=True)
class RegexPattern(AbstractPattern):
    regex: str

    def __post_init__(self):
        assert isinstance(self.regex, str), self.regex
        try:
            re.compile(self.regex)
        except re.error:
            assert False, f"invalid regex string: {self.regex!s}"

    def _fields_to_json(self) -> dict:
        return dict(
            **super()._fields_to_json(),
            regex=self.regex,
        )

    @classmethod
    def _json_to_fields(cls, body: dict):
        return dict(
            regex=body.pop("regex"),
            **super()._json_to_fields(body),
        )

    def __repr__(self):
        if self.is_expected:
            return f"r({self.regex!r})"
        else:
            return f"r!({self.regex!r})"

    @classmethod
    def create_default(cls, index: int) -> "RegexPattern":
        return cls(index=index, is_expected=True, regex="")

    def _to_regex(self) -> str:
        return self.regex


@dataclass(frozen=True)
class TextPattern(AbstractPattern):
    text: str
    is_multiple_space_ignored: bool
    is_word: bool

    def __post_init__(self):
        assert isinstance(self.text, str), self.text

    def _fields_to_json(self) -> dict:
        return dict(
            **super()._fields_to_json(),
            text=self.text,
            is_multiple_space_ignored=self.is_multiple_space_ignored,
            is_word=self.is_word
        )

    @classmethod
    def _json_to_fields(cls, body: dict):
        return dict(
            text=body.pop("text"),
            is_multiple_space_ignored=body.pop("is_multiple_space_ignored"),
            is_word=body.pop("is_word"),
            **super()._json_to_fields(body),
        )

    def __repr__(self):
        if self.is_expected:
            return f"s({self.text!r})"
        else:
            return f"s!({self.text!r})"

    @classmethod
    def create_default(cls, index: int) -> "TextPattern":
        return cls(index=index, is_expected=True, text="", is_multiple_space_ignored=True,
                   is_word=False)

    def _to_regex(self) -> str:
        text = self.text
        tokens = re.findall(r"\s+|\S+", text)
        if self.is_multiple_space_ignored:
            regex_tokens = []
            for token in tokens:
                if re.fullmatch(r"\s+", token):
                    regex_tokens.append(r"\s+")
                else:
                    regex_tokens.append(re.escape(token))
            regex = "".join(regex_tokens)
        else:
            regex = re.escape(text)
        if self.is_word:
            regex = rf"\b{regex}\b"
        return regex


@dataclass(frozen=True)
class SpacePattern(AbstractPattern):
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
            return f"space()"
        else:
            return f"space!()"

    @classmethod
    def create_default(cls, index: int) -> "SpacePattern":
        return cls(index=index, is_expected=True)

    def _to_regex(self) -> str:
        return r"\s+"


@dataclass(frozen=True)
class EOLPattern(AbstractPattern):
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
            return f"eol()"
        else:
            return f"eol!()"

    @classmethod
    def create_default(cls, index: int) -> "EOLPattern":
        return cls(index=index, is_expected=True)

    def _to_regex(self) -> str:
        return r"\n"


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

    def to_regex_pattern(self, *, ignore_case: bool) -> tuple[str, int]:  # pattern and flags
        pattern_regex_lst = []
        for pattern in self:
            regex = pattern.to_regex_with_group()
            pattern_regex_lst.append(regex)

        total_regex = r".*?" + r".*?".join(pattern_regex_lst) + r".*?"

        flags = re.DOTALL | re.MULTILINE
        if ignore_case:
            flags |= re.IGNORECASE

        return total_regex, flags
