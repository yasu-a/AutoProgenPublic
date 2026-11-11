import importlib.metadata
from pathlib import Path
import tomllib

import pytest

from autoprogen.domain.model.app_version import AppVersion, ReleaseType
from autoprogen.infra.repository import app_version as app_version_module
from autoprogen.infra.repository.app_version import AppVersionRepository


def test_installed_version_matches_pyproject() -> None:
    """実行時メタデータがpyproject.tomlのバージョンと一致することを確認する。"""
    pyproject_fullpath = Path(__file__).parents[1] / "pyproject.toml"
    pyproject = tomllib.loads(pyproject_fullpath.read_text(encoding="utf-8"))

    assert importlib.metadata.version("autoprogen") == pyproject["project"]["version"]


@pytest.mark.parametrize(
    ("metadata_version", "expected"),
    [
        ("1.2.3", AppVersion(1, 2, ReleaseType.STABLE, 3)),
        ("1.2.0a4", AppVersion(1, 2, ReleaseType.ALPHA, 4)),
        ("1.2.0b5", AppVersion(1, 2, ReleaseType.BETA, 5)),
    ],
)
def test_app_version_repository_converts_package_metadata(
        monkeypatch: pytest.MonkeyPatch,
        metadata_version: str,
        expected: AppVersion,
) -> None:
    """配布メタデータを従来のAppVersion表現へ変換できることを確認する。"""
    monkeypatch.setattr(
        app_version_module.importlib.metadata,
        "version",
        lambda distribution_name: metadata_version,
    )

    assert AppVersionRepository().get() == expected


def test_app_version_repository_uses_development_version_when_not_installed(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """配布メタデータがない開発環境では0.0.0として起動できることを確認する。"""
    def _raise_package_not_found(distribution_name: str) -> str:
        """テスト対象へパッケージ未インストール状態を返す。"""
        raise importlib.metadata.PackageNotFoundError(distribution_name)

    monkeypatch.setattr(
        app_version_module.importlib.metadata,
        "version",
        _raise_package_not_found,
    )

    assert AppVersionRepository().get() == AppVersion(
        major=0,
        minor=0,
        release_type=ReleaseType.STABLE,
        patch=0,
    )


def test_app_version_keeps_project_json_format() -> None:
    """既存プロジェクトで使用するJSON形式を変更していないことを確認する。"""
    json_body = {
        "major": 1,
        "minor": 1,
        "release_type": "beta",
        "patch": 5,
    }

    app_version = AppVersion.from_json(json_body)

    assert app_version.to_json() == json_body
    assert str(app_version) == "1.1-beta.5"


def test_app_version_keeps_project_compatibility_check() -> None:
    """保存済みプロジェクトに対する従来の互換性判定を維持する。"""
    current_version = AppVersion(1, 1, ReleaseType.BETA, 5)
    older_project_version = AppVersion(1, 1, ReleaseType.BETA, 4)
    newer_project_version = AppVersion(1, 1, ReleaseType.BETA, 6)

    assert AppVersion.is_compatible(
        current_version=current_version,
        target_version=older_project_version,
    )
    assert not AppVersion.is_compatible(
        current_version=current_version,
        target_version=newer_project_version,
    )
