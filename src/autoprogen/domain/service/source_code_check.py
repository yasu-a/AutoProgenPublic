import hashlib
import re
from dataclasses import dataclass

from autoprogen.domain.model.source_code_check import (
    SourceCodeCheckCatalog,
    SourceCodeCheckEntry,
    SourceCodeCheckFinding,
    SourceCodeCheckMatchType,
    SourceCodeCheckResult,
)
from autoprogen.util.app_logging import create_logger


@dataclass(frozen=True)
class _StringLiteral:
    """字句解析中に抽出した一つの文字列リテラルを保持する。"""

    # 引用符を除いた、エスケープ表現を維持した文字列内容。
    content: str
    # 文字列内容のソースコード全体における開始位置。
    content_start: int


@dataclass(frozen=True)
class _LexicalView:
    """検出対象ごとに不要な字句を隠したソースコード表現を保持する。"""

    # コメント、文字列、文字リテラルを空白化し、位置を維持したソースコード。
    code_only: str
    # コメントだけを空白化し、プリプロセッサ解析に使用するソースコード。
    without_comments: str
    # ソースコードから抽出した文字列リテラル。
    string_literals: tuple[_StringLiteral, ...]


class SourceCodeCheckDecodeError(UnicodeError):
    """コンパイル対象をUTF-8ソースコードとして解釈できない場合のエラー。"""


class SourceCodeCheckService:
    """コンパイル対象ソースへ静的安全性チェックを適用する。"""

    _logger = create_logger()
    _IDENTIFIER_CHARACTER_PATTERN = r"A-Za-z0-9_"

    @staticmethod
    def _mask_character(characters: list[str], index: int) -> None:
        """行位置を維持したまま、指定位置の字句を空白化する。"""
        if characters[index] not in "\r\n":
            characters[index] = " "

    @classmethod
    def _create_lexical_view(cls, source_code_text: str) -> _LexicalView:
        """コメントやリテラルを区別した検査用ソースコードを生成する。"""
        code_only = list(source_code_text)
        without_comments = list(source_code_text)
        string_literals: list[_StringLiteral] = []
        index = 0

        while index < len(source_code_text):
            current = source_code_text[index]
            following = source_code_text[index +
                                         1] if index + 1 < len(source_code_text) else ""

            # 行コメントは改行を残して両方の検査用表現から除外する。
            if current == "/" and following == "/":
                while index < len(source_code_text) and source_code_text[index] not in "\r\n":
                    cls._mask_character(code_only, index)
                    cls._mask_character(without_comments, index)
                    index += 1
                continue

            # ブロックコメントは内部の改行位置を維持して除外する。
            if current == "/" and following == "*":
                cls._mask_character(code_only, index)
                cls._mask_character(without_comments, index)
                index += 1
                cls._mask_character(code_only, index)
                cls._mask_character(without_comments, index)
                index += 1
                while index < len(source_code_text):
                    if (
                            source_code_text[index] == "*"
                            and index + 1 < len(source_code_text)
                            and source_code_text[index + 1] == "/"
                    ):
                        cls._mask_character(code_only, index)
                        cls._mask_character(without_comments, index)
                        index += 1
                        cls._mask_character(code_only, index)
                        cls._mask_character(without_comments, index)
                        index += 1
                        break
                    cls._mask_character(code_only, index)
                    cls._mask_character(without_comments, index)
                    index += 1
                continue

            # 文字列リテラルは内容を記録し、関数呼び出し用の表現だけから除外する。
            if current == '"':
                cls._mask_character(code_only, index)
                index += 1
                content_start = index
                while index < len(source_code_text):
                    if source_code_text[index] == "\\":
                        cls._mask_character(code_only, index)
                        index += 1
                        if index < len(source_code_text):
                            cls._mask_character(code_only, index)
                            index += 1
                        continue
                    if source_code_text[index] == '"':
                        content = source_code_text[content_start:index]
                        string_literals.append(
                            _StringLiteral(content, content_start))
                        cls._mask_character(code_only, index)
                        index += 1
                        break
                    cls._mask_character(code_only, index)
                    index += 1
                continue

            # 文字リテラルは関数名検出の対象外とし、内容は危険文字列として扱わない。
            if current == "'":
                cls._mask_character(code_only, index)
                index += 1
                while index < len(source_code_text):
                    if source_code_text[index] == "\\":
                        cls._mask_character(code_only, index)
                        index += 1
                        if index < len(source_code_text):
                            cls._mask_character(code_only, index)
                            index += 1
                        continue
                    is_end = source_code_text[index] == "'"
                    cls._mask_character(code_only, index)
                    index += 1
                    if is_end:
                        break
                continue

            index += 1

        return _LexicalView(
            code_only="".join(code_only),
            without_comments="".join(without_comments),
            string_literals=tuple(string_literals),
        )

    @staticmethod
    def _line_number(source_code_text: str, position: int) -> int:
        """文字位置を1から始まる行番号へ変換する。"""
        return source_code_text.count("\n", 0, position) + 1

    @staticmethod
    def _create_finding(
            *,
            group_id: str,
            entry: SourceCodeCheckEntry,
            line_number: int,
    ) -> SourceCodeCheckFinding:
        """チェック規則と一致箇所から構造化された検出結果を生成する。"""
        return SourceCodeCheckFinding(
            line_number=line_number,
            group_id=group_id,
            check_id=entry.check_id,
        )

    @classmethod
    def _find_function_calls(
            cls,
            *,
            group_id: str,
            entry: SourceCodeCheckEntry,
            source_code_text: str,
            code_only: str,
    ) -> list[SourceCodeCheckFinding]:
        """コメントやリテラル以外にある対象関数の呼び出しを検出する。"""
        findings: list[SourceCodeCheckFinding] = []
        for target in entry.target_strings:
            optional_windows_suffix = "(?:A|W)?" if target[0].isupper() else ""
            pattern = re.compile(
                rf"(?<![{cls._IDENTIFIER_CHARACTER_PATTERN}])"
                rf"(?P<name>{re.escape(target)}{optional_windows_suffix})"
                rf"(?=\s*\()"
            )
            for match in pattern.finditer(code_only):
                findings.append(cls._create_finding(
                    group_id=group_id,
                    entry=entry,
                    line_number=cls._line_number(
                        source_code_text, match.start("name")),
                ))
        return findings

    @classmethod
    def _find_dangerous_strings(
            cls,
            *,
            group_id: str,
            entry: SourceCodeCheckEntry,
            source_code_text: str,
            string_literals: tuple[_StringLiteral, ...],
    ) -> list[SourceCodeCheckFinding]:
        """文字列リテラル内にある危険なコマンドやパスを検出する。"""
        findings: list[SourceCodeCheckFinding] = []
        for literal in string_literals:
            lowered_content = literal.content.casefold()
            for target in entry.target_strings:
                # C文字列内のバックスラッシュはエスケープされる場合も同一対象として扱う。
                candidates = {target, target.replace("\\", "\\\\")}
                for candidate in candidates:
                    start = 0
                    while True:
                        position = lowered_content.find(
                            candidate.casefold(), start)
                        if position < 0:
                            break
                        absolute_position = literal.content_start + position
                        findings.append(cls._create_finding(
                            group_id=group_id,
                            entry=entry,
                            line_number=cls._line_number(
                                source_code_text, absolute_position),
                        ))
                        start = position + max(len(candidate), 1)
        return findings

    @staticmethod
    def _iter_logical_lines(source_code_text: str) -> list[tuple[int, str]]:
        """行継続を結合したプリプロセッサ用の論理行を列挙する。"""
        logical_lines: list[tuple[int, str]] = []
        buffer = ""
        start_line = 1
        for line_number, physical_line in enumerate(source_code_text.splitlines(), start=1):
            stripped_line = physical_line.rstrip()
            if not buffer:
                start_line = line_number
            if stripped_line.endswith("\\"):
                buffer += stripped_line[:-1] + " "
                continue
            logical_lines.append((start_line, buffer + physical_line))
            buffer = ""
        if buffer:
            logical_lines.append((start_line, buffer))
        return logical_lines

    @classmethod
    def _find_preprocessor(
            cls,
            *,
            group_id: str,
            entry: SourceCodeCheckEntry,
            lexical_view: _LexicalView,
    ) -> list[SourceCodeCheckFinding]:
        """includeとpragmaに固有のプリプロセッサ規則を検査する。"""
        findings: list[SourceCodeCheckFinding] = []
        logical_lines = cls._iter_logical_lines(lexical_view.without_comments)
        for line_number, logical_line in logical_lines:
            include_match = re.match(
                r"^\s*#\s*include\s+(.+?)\s*$", logical_line)
            if entry.match_type == SourceCodeCheckMatchType.PREPROCESSOR_EXTERNAL_INCLUDE:
                if include_match is None:
                    continue
                argument = include_match.group(1)
                if not (
                        (argument.startswith('"') and argument.endswith('"'))
                        or (argument.startswith("<") and argument.endswith(">"))
                ):
                    continue
                path_text = argument[1:-1]
                is_external = bool(re.search(
                    r"(?:^|[\\/])\.\.(?:[\\/]|$)|^[A-Za-z]:[\\/]|^[\\/]",
                    path_text,
                ))
                if is_external:
                    findings.append(cls._create_finding(
                        group_id=group_id,
                        entry=entry,
                        line_number=line_number,
                    ))
            elif entry.match_type == SourceCodeCheckMatchType.PREPROCESSOR_MACRO_INCLUDE:
                if include_match is None:
                    continue
                argument = include_match.group(1)
                if not argument.startswith(('"', "<")):
                    findings.append(cls._create_finding(
                        group_id=group_id,
                        entry=entry,
                        line_number=line_number,
                    ))
            elif entry.match_type == SourceCodeCheckMatchType.PREPROCESSOR_PRAGMA:
                pragma_match = re.search(
                    r"#\s*pragma\s+comment\b", logical_line)
                if pragma_match is not None:
                    findings.append(cls._create_finding(
                        group_id=group_id,
                        entry=entry,
                        line_number=line_number,
                    ))

        if entry.match_type == SourceCodeCheckMatchType.PREPROCESSOR_PRAGMA:
            pragma_pattern = re.compile(
                r"\b(?:__pragma\s*\(\s*comment|_Pragma\s*\()")
            for match in pragma_pattern.finditer(lexical_view.code_only):
                findings.append(cls._create_finding(
                    group_id=group_id,
                    entry=entry,
                    line_number=cls._line_number(
                        lexical_view.code_only, match.start()),
                ))
        return findings

    @classmethod
    def _find_source_patterns(
            cls,
            *,
            group_id: str,
            entry: SourceCodeCheckEntry,
            source_code_text: str,
            code_only: str,
    ) -> list[SourceCodeCheckFinding]:
        """空白表記の差を許容して疑わしい構文を検出する。"""
        findings: list[SourceCodeCheckFinding] = []
        pattern = re.compile(
            r"\bwhile\s*\(\s*(?:1|true)\s*\)"
            r"|\bfor\s*\(\s*;\s*;\s*\)"
        )
        for match in pattern.finditer(code_only):
            findings.append(cls._create_finding(
                group_id=group_id,
                entry=entry,
                line_number=cls._line_number(source_code_text, match.start()),
            ))
        return findings

    @classmethod
    def _find_entry(
            cls,
            *,
            group_id: str,
            entry: SourceCodeCheckEntry,
            source_code_text: str,
            lexical_view: _LexicalView,
    ) -> list[SourceCodeCheckFinding]:
        """規則に指定された検出方式で一致箇所を探す。"""
        if entry.match_type == SourceCodeCheckMatchType.FUNCTION_CALL:
            return cls._find_function_calls(
                group_id=group_id,
                entry=entry,
                source_code_text=source_code_text,
                code_only=lexical_view.code_only,
            )
        if entry.match_type == SourceCodeCheckMatchType.STRING_LITERAL:
            return cls._find_dangerous_strings(
                group_id=group_id,
                entry=entry,
                source_code_text=source_code_text,
                string_literals=lexical_view.string_literals,
            )
        if entry.match_type in {
            SourceCodeCheckMatchType.PREPROCESSOR_EXTERNAL_INCLUDE,
            SourceCodeCheckMatchType.PREPROCESSOR_MACRO_INCLUDE,
            SourceCodeCheckMatchType.PREPROCESSOR_PRAGMA,
        }:
            return cls._find_preprocessor(
                group_id=group_id,
                entry=entry,
                lexical_view=lexical_view,
            )
        if entry.match_type == SourceCodeCheckMatchType.SOURCE_PATTERN:
            return cls._find_source_patterns(
                group_id=group_id,
                entry=entry,
                source_code_text=source_code_text,
                code_only=lexical_view.code_only,
            )
        raise ValueError(f"Unsupported match type: {entry.match_type}")

    def execute(
            self,
            *,
            source_code_bytes: bytes,
            catalog: SourceCodeCheckCatalog,
    ) -> SourceCodeCheckResult:
        """UTF-8ソースコードを検査し、SHA-256と検出結果を返す。"""
        source_sha256 = hashlib.sha256(source_code_bytes).hexdigest()
        try:
            source_code_text = source_code_bytes.decode(
                "utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise SourceCodeCheckDecodeError(
                "source code must be valid UTF-8"
            ) from error

        self._logger.info(
            "SOURCE CODE SAFETY CHECK STARTED "
            f"(source_size={len(source_code_bytes)}, "
            f"group_count={len(catalog.groups)}, "
            f"check_count={catalog.entry_count})"
        )

        lexical_view = self._create_lexical_view(source_code_text)
        findings = [
            finding
            for group in catalog.groups
            for entry in group.entries
            for finding in self._find_entry(
                group_id=group.group_id,
                entry=entry,
                source_code_text=source_code_text,
                lexical_view=lexical_view,
            )
        ]

        # 同一グループの同一規則が同じ行で複数回検出された場合は一件にまとめる。
        unique_findings = {
            (
                finding.group_id,
                finding.check_id,
                finding.line_number,
            ): finding
            for finding in findings
        }
        ordered_findings = tuple(sorted(
            unique_findings.values(),
            key=lambda finding: (
                finding.line_number,
                finding.group_id,
                finding.check_id,
            ),
        ))
        self._logger.info(
            "SOURCE CODE SAFETY CHECK FINISHED "
            f"(finding_count={len(ordered_findings)}, sha256={source_sha256})"
        )
        return SourceCodeCheckResult(
            source_sha256=source_sha256,
            findings=ordered_findings,
        )
