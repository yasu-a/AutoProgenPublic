import os
import sys
from typing import TYPE_CHECKING

from autoprogen.util import app_logging
from autoprogen.util.app_logging import create_logger

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QApplication

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


def main():
    _install_exception_hook()

    from autoprogen.application.container import AppContainer
    from autoprogen.application.state.debug import set_debug
    from autoprogen.control.navigator import Navigator
    from autoprogen.infra.path_layout import AppPathConfig

    # 環境変数からデバッグ用の構成を用意
    app_logging.set_level(app_logging.INFO)
    if os.getenv("APP_DEBUG", "").strip() == "1":
        set_debug(True)
        _logger.info("STARTING WITH DEBUG MODE")
        if os.getenv("APP_VERBOSE_LOG"):
            app_logging.set_level(app_logging.DEBUG)
            _logger.info("VERBOSE LOG ENABLED")

    app_container = AppContainer(
        app_path_config=AppPathConfig.production(),
    )
    # QApplicationを生成
    app = create_app(
        app_version_text=app_container.app_version_get_text_usecase.execute(),
    )
    app.setQuitOnLastWindowClosed(False)

    navigator = Navigator(app_container=app_container)
    if navigator.start():
        sys.exit(app.exec_())
