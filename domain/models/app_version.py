from dataclasses import dataclass
from enum import Enum


class ReleaseType(Enum):
    STABLE = "stable"  # 安定版
    ALPHA = "alpha"  # アルファ版
    BETA = "beta"  # ベータ版


@dataclass(frozen=True)
class AppVersion:
    major: int
    minor: int
    release_type: ReleaseType
    patch: int

    @property
    def is_stable(self) -> bool:
        return self.release_type == ReleaseType.STABLE

    def __str__(self) -> str:
        # バージョン文字列を返す
        # 例: 1.2.3（安定版），1.2-alpha.3（alpha or beta）
        if self.is_stable:
            return f"{self.major}.{self.minor}.{self.patch}"
        else:
            return f"{self.major}.{self.minor}-{self.release_type.value}.{self.patch}"

    @classmethod
    def from_json(cls, body):
        return cls(
            major=body["major"],
            minor=body["minor"],
            release_type=ReleaseType(body["release_type"]),
            patch=body["patch"],
        )
