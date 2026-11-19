import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import pytest

from autoprogen.domain.model.app_version import AppVersion, ReleaseType
from autoprogen.domain.model.global_settings import GlobalSettings
from autoprogen.infra.repository.global_settings import GlobalSettingsRepository


@pytest.mark.parametrize(
    "compiler_tool_fullpath",
    [None, Path(r"C:\Program Files\Microsoft Visual Studio\VsDevCmd.bat")],
)
def test_compiler_tool_fullpath_survives_json_round_trip(
        compiler_tool_fullpath: Path | None,
) -> None:
    """未設定と設定済みのコンパイラーパスをJSON往復後も維持する。"""
    settings = GlobalSettings.create_default(
        compiler_tool_fullpath=compiler_tool_fullpath,
    )

    json_body = json.loads(json.dumps(settings.to_json()))
    restored = GlobalSettings.from_json(json_body)

    assert restored == settings


def test_usage_notice_version_survives_json_round_trip() -> None:
    """最後に同意した注意事項のバージョンをJSON往復後も維持する。"""
    settings = GlobalSettings.create_default()
    settings.last_agreed_usage_notice_version = AppVersion(
        major=1,
        minor=2,
        release_type=ReleaseType.BETA,
        patch=1,
    )

    restored = GlobalSettings.from_json(
        json.loads(json.dumps(settings.to_json())),
    )

    assert restored.last_agreed_usage_notice_version == AppVersion(
        major=1,
        minor=2,
        release_type=ReleaseType.BETA,
        patch=1,
    )


def test_missing_usage_notice_version_is_loaded_as_not_agreed() -> None:
    """旧設定に同意バージョンがない場合は未同意として読み込む。"""
    old_json_body = GlobalSettings.create_default().to_json()
    del old_json_body["last_agreed_usage_notice_version"]

    restored = GlobalSettings.from_json(old_json_body)

    assert restored.last_agreed_usage_notice_version is None


def test_repository_keeps_cached_settings_when_write_fails(tmp_path: Path) -> None:
    """設定の永続化に失敗した場合はキャッシュを保存候補へ更新しない。"""
    default_settings = GlobalSettings.create_default()
    global_core_io = Mock()
    app_path_layout = Mock()
    app_path_layout.settings_json = tmp_path / "settings.json"
    repository = GlobalSettingsRepository(
        global_core_io=global_core_io,
        app_path_layout=app_path_layout,
        default_model=default_settings,
    )
    agreed_settings = replace(
        default_settings,
        last_agreed_usage_notice_version=AppVersion(
            major=1,
            minor=2,
            release_type=ReleaseType.BETA,
            patch=1,
        ),
    )
    global_core_io.write_json.side_effect = OSError("settings write failed")

    with pytest.raises(OSError, match="settings write failed"):
        repository.put(agreed_settings)

    assert repository.get() is default_settings
    assert repository.get().last_agreed_usage_notice_version is None
