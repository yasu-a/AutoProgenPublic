from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel

from autoprogen.res.font import get_font


class UnstableVersionNotificationStatusBarWidget(QWidget):
    """テスト版であることをメイン画面のステータスバーへ表示する。"""

    def __init__(
            self,
            parent: QObject = None,
    ) -> None:
        """テスト版を通知するラベルを構築する。"""
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        """テスト版の警告ラベルを配置する。"""
        self.setStyleSheet(
            "QLabel {"
            "   color: #ffffff;"
            "   background-color: #cc0000;"
            "   border-radius: 4px;"
            "   padding: 2px;"
            "}"
        )

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self._l_notif = QLabel(self)
        self._l_notif.setText("このバージョンはテスト版です")
        self._l_notif.setFont(get_font(small=True))
        layout.addWidget(self._l_notif)

    def set_data(self, is_stable: bool) -> None:
        """安定版では通知を隠し、テスト版では表示する。"""
        self.setVisible(not is_stable)
