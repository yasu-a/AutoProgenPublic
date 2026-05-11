from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel

from res.font import get_font
from usecase.app_version import AppVersionCheckIsStableUseCase


class UnstableVersionNotificationStatusBarWidget(QWidget):
    def __init__(self, parent: QObject = None, *, app_version_check_is_stable_usecase: AppVersionCheckIsStableUseCase):
        super().__init__(parent)
        self._app_version_check_is_stable_usecase = app_version_check_is_stable_usecase

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        is_stable = self._app_version_check_is_stable_usecase.execute()

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
