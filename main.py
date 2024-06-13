from PyQt5.QtWidgets import *

import state
from app_logging import create_logger
from fonts import font
from gui_main import MainWindow
from gui_welcome import WelcomeDialog

_logger = create_logger()

if __name__ == '__main__':
    import sys

    sys._excepthook = sys.excepthook


    def exception_hook(exctype, value, traceback):
        _logger.exception(exctype, value, traceback)
        print(exctype, value, traceback)
        # noinspection PyProtectedMember
        sys._excepthook(exctype, value, traceback)  # type: ignore
        sys.exit(1)


    sys.excepthook = exception_hook

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setFont(font())
    app.setStyle('Fusion')

    welcome = WelcomeDialog()
    if welcome.exec_() == QDialog.Accepted:
        state.setup_project(welcome.project_path, app)
        window = MainWindow()
        window.show()
        app.exec()
