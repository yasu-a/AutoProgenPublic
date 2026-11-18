import json
from pathlib import Path

import pytest

from autoprogen.domain.model.app_version import AppVersion, ReleaseType
from autoprogen.domain.model.global_settings import GlobalSettings


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
