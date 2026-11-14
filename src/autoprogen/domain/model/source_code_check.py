from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum


class SourceCodeCheckMatchType(Enum):
    """チェック規則ごとの検査対象と検出方式を表す。"""

    FUNCTION_CALL = "function_call"
    STRING_LITERAL = "string_literal"
    PREPROCESSOR_EXTERNAL_INCLUDE = "preprocessor_external_include"
    PREPROCESSOR_MACRO_INCLUDE = "preprocessor_macro_include"
    PREPROCESSOR_PRAGMA = "preprocessor_pragma"
    SOURCE_PATTERN = "source_pattern"


@dataclass(frozen=True)
class SourceCodeCheckEntry:
    """一つのソースコードチェック規則を表す。"""

    # 保存設定から規則を参照するための、所属グループ内で変更しない一意な識別子。
    check_id: str
    # 設定画面や検出結果に表示する規則名。
    name: str
    # 規則が検査する識別子や文字列。表記違いは同じ規則にまとめる。
    target_strings: tuple[str, ...]
    # 規則が検出する危険性や用途を説明する文章。
    description: str
    # コメントなどを区別して対象文字列を探すための検出方式。
    match_type: SourceCodeCheckMatchType = SourceCodeCheckMatchType.FUNCTION_CALL

    def __post_init__(self) -> None:
        """規則として不完全な値が生成されることを防ぐ。"""
        if not self.check_id:
            raise ValueError("check_id must not be empty")
        if not self.name:
            raise ValueError("name must not be empty")
        if not self.target_strings or any(not value for value in self.target_strings):
            raise ValueError("target_strings must contain non-empty strings")
        if not self.description:
            raise ValueError("description must not be empty")


@dataclass(frozen=True)
class SourceCodeCheckGroup:
    """同じ目的を持つソースコードチェック規則をまとめる。"""

    # 保存設定や画面上でグループを識別するための一意な識別子。
    group_id: str
    # 設定画面に表示するグループ名。
    name: str
    # このグループに属するチェック規則。空のグループは許可しない。
    entries: tuple[SourceCodeCheckEntry, ...]

    def __post_init__(self) -> None:
        """グループ内の規則IDが一意であることを保証する。"""
        if not self.group_id:
            raise ValueError("group_id must not be empty")
        if not self.name:
            raise ValueError("name must not be empty")
        if not self.entries:
            raise ValueError("entries must not be empty")
        check_ids = [entry.check_id for entry in self.entries]
        if len(check_ids) != len(set(check_ids)):
            raise ValueError("check_id must be unique within a group")


@dataclass(frozen=True)
class SourceCodeCheckCatalog:
    """AutoProgenが提供するソースコードチェック規則の全体構造を管理する。"""

    # 設定画面での表示順を維持したチェック規則グループ。
    groups: tuple[SourceCodeCheckGroup, ...]

    def __post_init__(self) -> None:
        """カタログ全体でグループIDが一意であることを保証する。"""
        group_ids = [group.group_id for group in self.groups]
        if len(group_ids) != len(set(group_ids)):
            raise ValueError("group_id must be unique")

    def filter(
            self,
            *,
            exclude: Iterable[tuple[str, str]],
    ) -> "SourceCodeCheckCatalog":
        """指定されたグループIDとチェックIDの組を除いた新しいカタログを返す。"""
        excluded_ids = set(exclude)
        groups: list[SourceCodeCheckGroup] = []
        for group in self.groups:
            entries = tuple(
                entry
                for entry in group.entries
                if (group.group_id, entry.check_id) not in excluded_ids
            )
            if entries:
                groups.append(SourceCodeCheckGroup(
                    group_id=group.group_id,
                    name=group.name,
                    entries=entries,
                ))
        return SourceCodeCheckCatalog(groups=tuple(groups))

    @property
    def entry_count(self) -> int:
        """カタログに登録されたチェック規則数を返す。"""
        return sum(len(group.entries) for group in self.groups)


@dataclass(frozen=True)
class SourceCodeCheckFinding:
    """一つのチェック規則によって検出されたソースコード上の問題を表す。"""

    # 該当箇所の1から始まる行番号。
    line_number: int
    # 問題を検出したチェックグループの識別子。
    group_id: str
    # グループ内で問題を検出したチェック規則の識別子。
    check_id: str


@dataclass(frozen=True)
class SourceCodeCheckResult:
    """一つのソースコードに対する静的安全性チェック結果を表す。"""

    # 実際に検査したソースコードの小文字16進表記SHA-256。
    source_sha256: str
    # 検出順に並べた問題。空の場合は問題が検出されていない。
    findings: tuple[SourceCodeCheckFinding, ...]

    @property
    def is_safe(self) -> bool:
        """問題が一件も検出されなかった場合にTrueを返す。"""
        return not self.findings
