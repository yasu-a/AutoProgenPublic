import os
import sys
from pathlib import Path
from pprint import pformat
from typing import TYPE_CHECKING

from autoprogen.util import app_logging
from autoprogen.util.app_logging import create_logger

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QApplication
    from autoprogen.domain.model.debug_settings import DebugSettings

_logger = create_logger()


def _install_exception_hook() -> None:
    original_exception_hook = sys.excepthook

    def exception_hook(exctype, value, traceback):
        print(exctype, value, traceback)
        original_exception_hook(exctype, value, traceback)
        sys.exit(1)

    sys.excepthook = exception_hook


def create_app(*, app_version_text: str) -> "QApplication":
    from PyQt5.QtWidgets import QApplication, QProxyStyle, QStyle
    from autoprogen.res.icon import get_icon
    from autoprogen.res.font import get_font

    class CustomStyle(QProxyStyle):
        # noinspection PyMethodOverriding
        def styleHint(self, hint, option, widget, return_data):
            if hint == QStyle.SH_ToolTip_WakeUpDelay:
                return 0  # ツールチップの表示遅延を0にする
            return super().styleHint(hint, option, widget, return_data)

    app = QApplication(sys.argv)
    app.setApplicationName("プロ言採点")
    app.setApplicationVersion(app_version_text)
    app.setWindowIcon(get_icon("app"))
    # noinspection PyArgumentList
    app.setFont(get_font())
    app.setStyle(CustomStyle("Fusion"))

    return app


def _load_debug_settings(
        *,
        debug_mode: bool,
        app_base_dir: Path,
) -> "DebugSettings":
    """起動モードに応じて開発者固有設定を読み込み、結果をログへ記録する。"""
    from autoprogen.domain.model.debug_settings import DebugSettings
    from autoprogen.infra.gateway.debug_settings_toml import DebugSettingsTomlGateway

    if not debug_mode:
        _logger.info("DEBUG SETTINGS NOT LOADED: debug mode is disabled")
        return DebugSettings.create_default()

    toml_fullpath = app_base_dir / ".autoprogen-dev.toml"
    if not toml_fullpath.exists():
        _logger.info(f"DEBUG SETTINGS NOT LOADED: file does not exist: {toml_fullpath!s}")
        return DebugSettings.create_default()

    debug_settings = DebugSettingsTomlGateway(
        toml_fullpath=toml_fullpath,
    ).read()
    _logger.info(
        "DEBUG SETTINGS LOADED"
        f"\n  file={toml_fullpath!s}"
        f"\n  settings={pformat(debug_settings, width=100, sort_dicts=False)}"
    )
    return debug_settings


def main() -> None:
    """実行環境の設定を読み込み、AutoProgenを起動する。"""
    _install_exception_hook()

    from autoprogen.application.container import AppContainer
    from autoprogen.control.navigator import Navigator
    from autoprogen.infra.path_layout import AppPathConfig

    # 環境変数からデバッグ用の構成を用意
    app_logging.set_level(app_logging.INFO)
    debug_mode = os.getenv("APP_DEBUG", "").strip() == "1"
    if debug_mode:
        _logger.info("STARTING WITH DEBUG MODE")
        if os.getenv("APP_VERBOSE_LOG"):
            app_logging.set_level(app_logging.DEBUG)
            _logger.info("VERBOSE LOG ENABLED")

    # 通常起動では入力補助を無効にし、デバッグ起動時だけ開発者固有のTOML設定を読み込む。
    app_path_config = AppPathConfig.production()
    debug_settings = _load_debug_settings(
        debug_mode=debug_mode,
        app_base_dir=app_path_config.app_base_dir,
    )

    # 起動時に確定した構成を依存関係の起点へ注入し、下流でのデバッグモード判定を避ける。
    app_container = AppContainer(
        app_path_config=app_path_config,
        debug_settings=debug_settings,
    )
    # QApplicationを生成
    app = create_app(
        app_version_text=app_container.app_version_get_text_usecase.execute(),
    )
    app.setQuitOnLastWindowClosed(False)

    navigator = Navigator(app_container=app_container)
    if navigator.start():
        sys.exit(app.exec_())
