from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel

from application.dependency.usecases import get_app_version_check_is_stable_usecase
from controls.res.fonts import get_font


class UnstableVersionNotificationStatusBarWidget(QWidget):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        is_stable = get_app_version_check_is_stable_usecase().execute()

        # noinspection PyUnresolvedReferences
        if not is_stable:
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

        if not is_stable:
            self._l_notif = QLabel(self)
            self._l_notif.setText("このバージョンはテスト版です")
            self._l_notif.setFont(get_font(small=True))
            layout.addWidget(self._l_notif)

    def _init_signals(self):
        pass
