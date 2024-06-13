from PyQt5.QtWidgets import *

import state
from fonts import font
from gui_main import MainWindow

if __name__ == '__main__':
    import sys

    sys._excepthook = sys.excepthook


    def exception_hook(exctype, value, traceback):
        print(exctype, value, traceback)
        # noinspection PyProtectedMember
        sys._excepthook(exctype, value, traceback)  # type: ignore
        sys.exit(1)


    sys.excepthook = exception_hook

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setFont(font())
    app.setStyle('Fusion')

    state.setup_project(
        "C:/Users/yasuh/OneDrive/デスクトップ/rep",
        app,
    )
    window = MainWindow()
    window.show()
    app.exec()
