from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QFrame, QWidget, QVBoxLayout


class HorizontalLineWidget(QWidget):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(layout)

        self._frame = QFrame(self)
        self._frame.setFrameShape(QFrame.HLine)
        self._frame.setFrameShadow(QFrame.Sunken)
        layout.addWidget(self._frame)

    def _init_signals(self):
        pass
