import os
from typing import TYPE_CHECKING

from util import app_logging
from util.app_logging import create_logger

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QApplication

if __name__ == '__main__':
    import sys

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
    from application.dependency.usecase import get_app_version_get_text_usecase
    from res.icon import get_icon
    from res.font import get_font

    class CustomStyle(QProxyStyle):
        # noinspection PyMethodOverriding
        def styleHint(self, hint, option, widget, return_data):
            if hint == QStyle.SH_ToolTip_WakeUpDelay:
                return 0  # ツールチップの表示遅延を0にする
            return super().styleHint(hint, option, widget, return_data)

    app = QApplication(sys.argv)
    app.setApplicationName("プロ言採点")
    app.setApplicationVersion(get_app_version_get_text_usecase().execute())
    app.setWindowIcon(get_icon("app"))
    # noinspection PyArgumentList
    app.setFont(get_font())
    app.setStyle(CustomStyle("Fusion"))

    return app


def main():
    from application.dependency.navigator import get_navigator
    from application.state.debug import set_debug

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
    app.setQuitOnLastWindowClosed(False)

    navigator = get_navigator()
    if navigator.start():
        sys.exit(app.exec_())


if __name__ == '__main__':
    main()
