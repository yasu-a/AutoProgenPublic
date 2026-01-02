from dataclasses import dataclass
from enum import Enum
from functools import total_ordering


class ReleaseType(Enum):
    ALPHA = "alpha"  # アルファ版
    BETA = "beta"  # ベータ版
    STABLE = "stable"  # 安定版

    def __lt__(self, other):
        return list(type(self)).index(self) < list(type(self)).index(other)


@dataclass(frozen=True)
@total_ordering
class AppVersion:
    major: int
    minor: int
    release_type: ReleaseType
    patch: int

    @classmethod
    def is_compatible(
            cls,
            *,
            current_version: "AppVersion",
            target_version: "AppVersion",
    ) -> bool:
        # メジャーが一致していなければ互換性なし
        if current_version.major != target_version.major:
            return False
        # マイナーが一致していなければ互換性なし
        if current_version.minor != target_version.minor:
            return False
        # リリースタイプが一致していなければ互換性なし
        if current_version.release_type != target_version.release_type:
            return False
        # 未来のパッチなら互換性なし
        if current_version.patch < target_version.patch:
            return False
        # それ以外は互換性あり
        return True

    @property
    def is_stable(self) -> bool:
        return self.release_type == ReleaseType.STABLE

    def __lt__(self, other):
        if not isinstance(other, AppVersion):
            return NotImplemented
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        if self.release_type != other.release_type:
            return self.release_type < other.release_type
        return self.patch < other.patch

    def __str__(self) -> str:
        # バージョン文字列を返す
        # 例: 1.2.3（安定版），1.2-alpha.3（alpha or beta）
        if self.is_stable:
            return f"{self.major}.{self.minor}.{self.patch}"
        else:
            return f"{self.major}.{self.minor}-{self.release_type.value}.{self.patch}"

    def to_json(self) -> dict:
        return dict(
            major=self.major,
            minor=self.minor,
            release_type=self.release_type.value,
            patch=self.patch,
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            major=body["major"],
            minor=body["minor"],
            release_type=ReleaseType(body["release_type"]),
            patch=body["patch"],
        )
