from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import QPushButton

from controls.res.fonts import get_font


class PageButton(QPushButton):
    def __init__(self, parent: QObject = None, *, text: str):
        super().__init__(parent)

        self._text = text

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        self.setText(self._text)
        self.setFont(get_font(monospace=True, large=True))
        self.setFixedWidth(60)
        self.setFixedHeight(30)
        self.setFocusPolicy(Qt.NoFocus)

    def _init_signals(self):
        pass
