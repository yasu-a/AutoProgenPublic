from pathlib import Path
from typing import Callable

import pytest

from autoprogen.application.container import AppContainer
from autoprogen.domain.model.debug_settings import DebugSettings
from autoprogen.infra.gateway.debug_settings_toml import (
    DebugSettingsGatewayError,
    DebugSettingsTomlGateway,
)
from autoprogen.infra.path_layout import AppPathConfig
from autoprogen.main import _load_debug_settings


def _write_debug_settings(toml_fullpath: Path) -> DebugSettings:
    """テスト用のデバッグ設定TOMLを書き込み、期待するモデルを返す。"""
    toml_fullpath.write_text(
        "\n".join([
            "compiler_tool_fullpath = 'C:\\Tools\\VsDevCmd.bat'",
            "report_archive_fullpath = 'C:\\TestData\\report.zip'",
            "auto_generate_project_name = true",
            "target_number = 4",
        ]),
        encoding="utf-8",
    )
    return DebugSettings(
        compiler_tool_fullpath=Path(r"C:\Tools\VsDevCmd.bat"),
        report_archive_fullpath=Path(r"C:\TestData\report.zip"),
        auto_generate_project_name=True,
        target_number=4,
    )


def test_debug_settings_toml_gateway_reads_all_values(tmp_path: Path) -> None:
    """TOMLの全項目をDebugSettingsへ変換する。"""
    toml_fullpath = tmp_path / ".autoprogen-dev.toml"
    expected = _write_debug_settings(toml_fullpath)

    actual = DebugSettingsTomlGateway(toml_fullpath=toml_fullpath).read()

    assert actual == expected


def test_debug_settings_toml_gateway_rejects_invalid_settings(tmp_path: Path) -> None:
    """TOMLとして読めてもドメイン制約を満たさない設定を拒否する。"""
    toml_fullpath = tmp_path / ".autoprogen-dev.toml"
    toml_fullpath.write_text("target_number = 100\n", encoding="utf-8")

    with pytest.raises(DebugSettingsGatewayError, match="0以上99以下"):
        DebugSettingsTomlGateway(toml_fullpath=toml_fullpath).read()


def test_debug_mode_applies_toml_settings(
        prepared_app_path_config: AppPathConfig,
        app_container_factory: Callable[..., AppContainer],
) -> None:
    """デバッグモードではTOMLを読み込み、アプリケーション構成へ反映する。"""
    expected = _write_debug_settings(
        prepared_app_path_config.app_base_dir / ".autoprogen-dev.toml",
    )

    debug_settings = _load_debug_settings(
        debug_mode=True,
        app_base_dir=prepared_app_path_config.app_base_dir,
    )
    app_container = app_container_factory(debug_settings=debug_settings)

    assert app_container.debug_settings == expected
    assert (
        app_container.global_settings_repository.get().compiler_tool_fullpath
        == expected.compiler_tool_fullpath
    )


def test_normal_mode_ignores_toml_settings(
        prepared_app_path_config: AppPathConfig,
        app_container_factory: Callable[..., AppContainer],
) -> None:
    """通常モードではTOMLが存在してもデバッグ用の値を反映しない。"""
    _write_debug_settings(
        prepared_app_path_config.app_base_dir / ".autoprogen-dev.toml",
    )

    debug_settings = _load_debug_settings(
        debug_mode=False,
        app_base_dir=prepared_app_path_config.app_base_dir,
    )
    app_container = app_container_factory(debug_settings=debug_settings)

    assert app_container.debug_settings == DebugSettings.create_default()
    assert app_container.global_settings_repository.get().compiler_tool_fullpath is None


def test_saved_global_settings_take_priority_over_debug_default(
        app_container_factory: Callable[..., AppContainer],
) -> None:
    """保存済みの利用者設定をデバッグ用の既定値で上書きしない。"""
    saved_compiler_tool_fullpath = Path(r"C:\Saved\VsDevCmd.bat")
    first_container = app_container_factory()
    saved_settings = first_container.global_settings_repository.get()
    saved_settings.compiler_tool_fullpath = saved_compiler_tool_fullpath
    first_container.global_settings_repository.put(saved_settings)

    second_container = app_container_factory(
        debug_settings=DebugSettings(
            compiler_tool_fullpath=Path(r"C:\Debug\VsDevCmd.bat"),
        ),
    )

    actual = second_container.global_settings_repository.get()

    assert actual.compiler_tool_fullpath == saved_compiler_tool_fullpath
