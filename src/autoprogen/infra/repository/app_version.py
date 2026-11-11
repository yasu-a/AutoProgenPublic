import importlib.metadata
import re

from autoprogen.domain.model.app_version import AppVersion
from autoprogen.domain.model.app_version import ReleaseType


_DISTRIBUTION_NAME = "autoprogen"
_DEVELOPMENT_VERSION = "0.0.0"
_PEP_440_VERSION_PATTERN = re.compile(
    r"(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
    r"(?:(?P<prerelease_type>a|b)(?P<prerelease_number>\d+))?"
)


class AppVersionRepository:
    """インストール済みパッケージのメタデータから実行時バージョンを取得する。"""

    def get(self) -> AppVersion:
        """配布メタデータのPEP 440バージョンをアプリ内の形式へ変換する。"""
        try:
            version_text = importlib.metadata.version(_DISTRIBUTION_NAME)
        except importlib.metadata.PackageNotFoundError:
            # 未インストールのソースツリーから実行した場合は開発用バージョンとして扱う。
            version_text = _DEVELOPMENT_VERSION

        return _convert_pep_440_version(version_text)


def _convert_pep_440_version(version_text: str) -> AppVersion:
    """対応するPEP 440表記を既存のAppVersionへ変換する。"""
    match = _PEP_440_VERSION_PATTERN.fullmatch(version_text)
    if match is None:
        raise ValueError(f"Unsupported application version: {version_text}")

    major = int(match.group("major"))
    minor = int(match.group("minor"))
    patch = int(match.group("patch"))
    prerelease_type = match.group("prerelease_type")
    prerelease_number = match.group("prerelease_number")

    if prerelease_type is None:
        return AppVersion(
            major=major,
            minor=minor,
            release_type=ReleaseType.STABLE,
            patch=patch,
        )

    if patch != 0 or prerelease_number is None:
        raise ValueError(f"Unsupported application prerelease version: {version_text}")

    release_type = {
        "a": ReleaseType.ALPHA,
        "b": ReleaseType.BETA,
    }[prerelease_type]
    return AppVersion(
        major=major,
        minor=minor,
        release_type=release_type,
        patch=int(prerelease_number),
    )
