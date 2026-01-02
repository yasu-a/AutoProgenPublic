from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout

from shared.view.style.font import get_font
from shared.view.widget_progress_icon import ProgressIconWidget


class WaitDialog(QDialog):
    """純粋な表示用ダイアログ - スレッド管理機能なし"""

    def __init__(self, parent=None, title: str = "処理中", message: str = ""):
        super().__init__(parent)
        self.__title = title
        self.__message = message
        self._init_ui()

    def _init_ui(self):
        self.setModal(True)
        self.setMinimumWidth(700)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        self.setLayout(layout)

        self._w_progress_icon = ProgressIconWidget(self)
        layout.addWidget(self._w_progress_icon)

        layout_message = QVBoxLayout()
        layout.addLayout(layout_message)

        self._l_title = QLabel(self)
        self._l_title.setFont(get_font(bold=True))
        self._l_title.setText(self.__title)
        layout_message.addWidget(self._l_title)

        self._l_message = QLabel(self)
        self._l_message.setWordWrap(True)
        self._l_message.setText(self.__message)
        layout_message.addWidget(self._l_message)

        layout_message.addStretch(1)

    def set_message(self, message: str):
        """メッセージを更新"""
        self._l_message.setText(message)
