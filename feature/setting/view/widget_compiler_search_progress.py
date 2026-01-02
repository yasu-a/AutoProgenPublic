from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

from shared.view.style.font import get_font


class CompilerSearchProgressWidget(QWidget):
    """検索進捗表示用ウィジェット"""

    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("検索中・・・ "))

        self._l_progress = QLabel(self)
        self._l_progress.setFont(get_font(monospace=True, small=True))
        layout.addWidget(self._l_progress)

    def set_progress_text(self, text: str) -> None:
        """進捗テキストを設定"""
        self._l_progress.setText(text)

