import copy
import itertools
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import NamedTuple, Iterable


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
    def to_regex(self) -> str:
        raise NotImplementedError()

    @property
    def regex_group_name(self) -> str:
        return f"_{self.index}"

    def to_regex_with_group(self):
        return "(?P<" + self.regex_group_name + ">" + self.to_regex() + ")"


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

    def to_regex(self) -> str:
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

    def to_regex(self) -> str:
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

    def to_regex(self) -> str:
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

    def to_regex(self) -> str:
        return r"\n"


class AbstractPatternList(ABC):
    def __init__(self, patterns: tuple[AbstractPattern, ...]):
        self._patterns: tuple[AbstractPattern, ...] = patterns

    @property
    def first_pattern_index(self) -> int:
        if self._patterns:
            return self._patterns[0].index
        else:
            raise ValueError("no patterns")

    @property
    def last_pattern_index(self) -> int:
        if self._patterns:
            return self._patterns[-1].index
        else:
            raise ValueError("no patterns")

    def __len__(self):
        return len(self._patterns)

    def __iter__(self):
        for pattern in self._patterns:
            yield copy.deepcopy(pattern)

    def __hash__(self) -> int:
        return hash((type(self), *self))

    def to_regex_pattern(self, *, ignore_case: bool) -> tuple[str, int]:  # pattern and flags
        pattern_regex_lst = []
        for pattern in self._patterns:
            regex = pattern.to_regex_with_group()
            pattern_regex_lst.append(regex)

        if pattern_regex_lst:
            total_regex = r".*?" + r".*?".join(pattern_regex_lst) + r".*?"
        else:
            total_regex = r".*?"

        flags = re.DOTALL | re.MULTILINE
        if ignore_case:
            flags |= re.IGNORECASE

        return total_regex, flags


class PatternList(AbstractPatternList):  # immutable
    def __init__(self, it: Iterable[AbstractPattern] = ()):
        super().__init__(tuple(it))

        if self._patterns:
            for i, pattern in enumerate(self._patterns):
                assert pattern.index == i, (pattern.index, i)

    def to_json(self):
        return dict(
            patterns=[pattern.to_json() for pattern in self._patterns]
        )

    @classmethod
    def from_json(cls, body):
        return cls(AbstractPattern.from_json(p) for p in body["patterns"])

    @property
    def expected_patterns(self) -> "DiscontinuousSubPatternList":
        """期待されるパターンで構成されるPatternListを取得"""
        return DiscontinuousSubPatternList([p for p in self if p.is_expected])

    def iter_unexpected_patterns(self) -> "Iterable[ContinuousSubPatternList]":
        """期待されないパターンで構成されるPatternListを連番を1グループとしてグループごとに順番に返す"""
        if not self._patterns:
            return

        slice_lst = []
        if self.expected_patterns._patterns[0].index != 0:
            slice_lst.append(slice(0, self.expected_patterns._patterns[0].index))
        for p in itertools.pairwise(self.expected_patterns):
            slice_lst.append(slice(p[0].index + 1, p[1].index))
        if self.expected_patterns._patterns[-1].index != len(self) - 1:
            slice_lst.append(slice(self.expected_patterns._patterns[-1].index + 1, len(self)))

        for s in slice_lst:
            if s.start == s.stop:
                continue
            yield ContinuousSubPatternList(self._patterns[s])


class DiscontinuousSubPatternList(AbstractPatternList):  # immutable
    def __init__(self, it: Iterable[AbstractPattern]):
        super().__init__(tuple(it))

        if self._patterns:
            for p_1, p_2 in itertools.pairwise(self._patterns):
                assert p_1.index < p_2.index, (p_1, p_2)


class ContinuousSubPatternList(AbstractPatternList):
    def __init__(self, it: tuple[AbstractPattern, ...]):
        super().__init__(tuple(it))

        if self._patterns:
            for p_1, p_2 in itertools.pairwise(self._patterns):
                assert p_1.index + 1 == p_2.index, (p_1, p_2)
