from PyQt5.QtCore import QObject, QTimer, pyqtSlot, Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

from controls.res.fonts import get_font


class ProgressIconWidget(QWidget):
    ICON_CHARS = (
        "o    ",
        " o   ",
        "  o  ",
        "   o ",
        "    o",
        "   o ",
        "  o  ",
        " o   ",
    )

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._timeout_count = 0

        self._timer = QTimer()
        self._timer.setInterval(100)
        self._timer.start()

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        self.setFixedWidth(50)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        layout.addStretch(1)

        self._l_text = QLabel(self)
        self._l_text.setAlignment(Qt.AlignCenter)
        self._l_text.setFont(get_font(monospace=True))
        self._l_text.setWordWrap(True)
        layout.addWidget(self._l_text)

        layout.addStretch(1)

    def _init_signals(self):
        # noinspection PyUnresolvedReferences
        self._timer.timeout.connect(self.__timer_timeout)

    @pyqtSlot()
    def __timer_timeout(self):
        self._timeout_count += 1
        self._l_text.setText(self.ICON_CHARS[self._timeout_count % len(self.ICON_CHARS)])
