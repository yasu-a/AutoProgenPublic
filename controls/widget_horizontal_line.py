from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QFrame


class HorizontalLineWidget(QFrame):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

    def _init_signals(self):
        pass
