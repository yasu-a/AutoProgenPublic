from PyQt5.QtCore import QObject, QTimer, pyqtSlot, Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

from fonts import font


class ProgressIconWidget(QWidget):
    ICON_CHARS = (
        "|     |",
        "|>    |",
        "|=>   |",
        "|==>  |",
        "|===> |",
        "|====>|",
    )

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._timeout_count = 0

        self._init_ui()
        self._init_signals()

        self._timer.start()

    def _init_ui(self):
        self.setFixedWidth(50)

        self._timer = QTimer()
        self._timer.setInterval(166)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self._l_text = QLabel(self)
        self._l_text.setAlignment(Qt.AlignCenter)
        self._l_text.setFont(font(monospace=True))
        layout.addWidget(self._l_text)

    def _init_signals(self):
        # noinspection PyUnresolvedReferences
        self._timer.timeout.connect(self.__timer_timeout)

    @pyqtSlot()
    def __timer_timeout(self):
        self._timeout_count += 1
        self._l_text.setText(self.ICON_CHARS[self._timeout_count % len(self.ICON_CHARS)])
