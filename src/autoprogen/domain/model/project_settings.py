import re
from dataclasses import dataclass

from autoprogen.domain.model.value import StudentID


@dataclass(frozen=True)
class SourceCodeCheckIdentifier:
    """プロジェクト設定から一つのソースコードチェック規則を参照する。"""

    # チェック規則が所属するグループの識別子。
    group_id: str
    # 所属グループ内で一意なチェック規則の識別子。
    check_id: str

    def __post_init__(self) -> None:
        """識別子に空文字列やグループIDを含むチェックIDを許可しない。"""
        if not isinstance(self.group_id, str):
            raise TypeError("group_idにはstrを指定してください")
        if not self.group_id:
            raise ValueError("group_idは空にできません")
        if not isinstance(self.check_id, str):
            raise TypeError("check_idにはstrを指定してください")
        if not self.check_id:
            raise ValueError("check_idは空にできません")
        if "." in self.check_id:
            raise ValueError("check_idにgroup_idを含めないでください")

    def to_json(self) -> dict[str, str]:
        """識別子をJSONへ保存できる辞書に変換する。"""
        return {
            "group_id": self.group_id,
            "check_id": self.check_id,
        }

    @classmethod
    def from_json(cls, body: dict) -> "SourceCodeCheckIdentifier":
        """JSONから読み込んだ辞書を識別子へ変換する。"""
        return cls(
            group_id=body["group_id"],
            check_id=body["check_id"],
        )


@dataclass(frozen=True)
class SourceCodeCheckSkip:
    """特定の学生が提出した特定のソースコードをチェック対象外として識別する。"""

    # チェックを省略する学生の学籍番号。
    student_id: StudentID
    # チェックを省略するソースコードの小文字16進表記SHA-256。
    source_sha256: str

    def __post_init__(self) -> None:
        """学籍番号の型とSHA-256の表記を検証する。"""
        if not isinstance(self.student_id, StudentID):
            raise TypeError("student_idにはStudentIDを指定してください")
        if not isinstance(self.source_sha256, str):
            raise TypeError("source_sha256にはstrを指定してください")
        if re.fullmatch(r"[0-9a-f]{64}", self.source_sha256) is None:
            raise ValueError("source_sha256には小文字16進表記のSHA-256を指定してください")

    def to_json(self) -> dict[str, str]:
        """チェック省略情報をJSONへ保存できる辞書に変換する。"""
        return {
            "student_id": self.student_id.to_json(),
            "source_sha256": self.source_sha256,
        }

    @classmethod
    def from_json(cls, body: dict) -> "SourceCodeCheckSkip":
        """JSONから読み込んだ辞書をチェック省略情報へ変換する。"""
        return cls(
            student_id=StudentID.from_json(body["student_id"]),
            source_sha256=body["source_sha256"],
        )


@dataclass(frozen=True)
class ProjectSettings:
    """一つのプロジェクトにだけ適用する設定を保持する。"""

    # プロジェクト内で無効にするソースコードチェック規則の識別子。
    disabled_source_code_checks: frozenset[SourceCodeCheckIdentifier]
    # 学生とソースコードの組み合わせごとに保存したチェック省略情報。
    source_code_check_skips: frozenset[SourceCodeCheckSkip]

    def __post_init__(self) -> None:
        """プロジェクト設定のフィールド型を検証する。"""
        if not isinstance(self.disabled_source_code_checks, frozenset):
            raise TypeError("disabled_source_code_checksにはfrozensetを指定してください")
        if any(
                not isinstance(identifier, SourceCodeCheckIdentifier)
                for identifier in self.disabled_source_code_checks
        ):
            raise TypeError(
                "disabled_source_code_checksの要素には"
                "SourceCodeCheckIdentifierを指定してください"
            )
        if not isinstance(self.source_code_check_skips, frozenset):
            raise TypeError("source_code_check_skipsにはfrozensetを指定してください")
        if any(
                not isinstance(skip, SourceCodeCheckSkip)
                for skip in self.source_code_check_skips
        ):
            raise TypeError(
                "source_code_check_skipsの要素にはSourceCodeCheckSkipを指定してください"
            )

    @classmethod
    def create_default(cls) -> "ProjectSettings":
        """すべてのソースコードチェック規則を有効にした既定設定を返す。"""
        return cls(
            disabled_source_code_checks=frozenset(),
            source_code_check_skips=frozenset(),
        )

    def with_source_code_check_skip(
            self,
            *,
            student_id: StudentID,
            source_sha256: str,
    ) -> "ProjectSettings":
        """指定した学生とソースコードの組をチェック省略対象へ追加する。"""
        skip = SourceCodeCheckSkip(
            student_id=student_id,
            source_sha256=source_sha256,
        )
        return ProjectSettings(
            disabled_source_code_checks=self.disabled_source_code_checks,
            source_code_check_skips=self.source_code_check_skips | {skip},
        )

    def to_json(self) -> dict[str, list[dict[str, str]]]:
        """設定値をJSONへ保存できる辞書に変換する。"""
        identifiers = sorted(
            self.disabled_source_code_checks,
            key=lambda identifier: (identifier.group_id, identifier.check_id),
        )
        skips = sorted(
            self.source_code_check_skips,
            key=lambda skip: (str(skip.student_id), skip.source_sha256),
        )
        return {
            "disabled_source_code_checks": [
                identifier.to_json()
                for identifier in identifiers
            ],
            "source_code_check_skips": [
                skip.to_json()
                for skip in skips
            ],
        }

    @classmethod
    def from_json(cls, body: dict) -> "ProjectSettings":
        """JSONから読み込んだ辞書をプロジェクト設定へ変換する。"""
        return cls(
            disabled_source_code_checks=frozenset(
                SourceCodeCheckIdentifier.from_json(identifier)
                for identifier in body["disabled_source_code_checks"]
            ),
            source_code_check_skips=frozenset(
                SourceCodeCheckSkip.from_json(skip)
                for skip in body.get("source_code_check_skips", [])
            ),
        )
