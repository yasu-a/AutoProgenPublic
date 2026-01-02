import os
import sys
from typing import TYPE_CHECKING

from util import app_logging
from util.app_logging import create_logger

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QApplication

if __name__ == '__main__':
    sys._excepthook = sys.excepthook


    def exception_hook(exctype, value, traceback):
        print(exctype, value, traceback)
        # noinspection PyProtectedMember
        sys._excepthook(exctype, value, traceback)  # type: ignore
        sys.exit(1)


    sys.excepthook = exception_hook

_logger = create_logger()


def create_app() -> "QApplication":
    from PyQt5.QtWidgets import QApplication, QProxyStyle, QStyle
    from app.di.provider import get_app_name_provider, get_app_version_provider
    from shared.view.style.icon import get_icon
    from shared.view.style.font import get_font

    class CustomStyle(QProxyStyle):
        # noinspection PyMethodOverriding
        def styleHint(self, hint, option, widget, return_data):
            if hint == QStyle.SH_ToolTip_WakeUpDelay:
                return 0  # ツールチップの表示遅延を0にする
            return super().styleHint(hint, option, widget, return_data)

    app = QApplication(sys.argv)
    app.setApplicationName(get_app_name_provider().provide())
    app.setApplicationVersion(str(get_app_version_provider().provide()))
    app.setWindowIcon(get_icon("app"))
    # noinspection PyArgumentList
    app.setFont(get_font())
    app.setStyle(CustomStyle("Fusion"))

    return app


def main():
    from app.state.debug import set_debug
    from app.di.app import get_navigator

    # 環境変数からデバッグ用の構成を用意
    app_logging.set_level(app_logging.INFO)
    if os.getenv("APP_DEBUG"):
        set_debug(True)
        _logger.info("STARTING WITH DEBUG MODE")
        if os.getenv("APP_VERBOSE_LOG"):
            app_logging.set_level(app_logging.DEBUG)
            _logger.info("VERBOSE LOG ENABLED")

    # QApplicationを生成
    app = create_app()

    # ★重要: メインウィンドウを閉じてもアプリを終了させない（Navigatorが制御する）
    app.setQuitOnLastWindowClosed(False)

    # Navigatorに制御を委譲（Windowは渡さない）
    navigator = get_navigator()
    navigator.start()

    # イベントループ開始
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
