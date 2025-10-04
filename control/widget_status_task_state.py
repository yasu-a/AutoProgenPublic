from PyQt5.QtCore import QObject, QTimer, pyqtSlot
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel

from application.dependency.task import get_task_manager
from res.font import get_font


class TaskStateStatusBarWidget(QWidget):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self.__icon_anim_state = 0

        self._icon_timer = QTimer(self)
        self._icon_timer.setInterval(100)

        self._update_timer = QTimer(self)
        self._update_timer.setInterval(1000)

        self._init_ui()
        self._init_signals()

        self._icon_timer.start()
        self._update_timer.start()

    def _init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self._l_icon = QLabel(self)
        self._l_icon.setFont(get_font(monospace=True))
        layout.addWidget(self._l_icon)

        self._l_message = QLabel(self)
        self._l_message.setEnabled(False)
        layout.addWidget(self._l_message)

    def _init_signals(self):
        # noinspection PyUnresolvedReferences
        self._icon_timer.timeout.connect(self.__icon_timer_timeout)
        # noinspection PyUnresolvedReferences
        self._update_timer.timeout.connect(self.__update_timer_timeout)

    @pyqtSlot()
    def __icon_timer_timeout(self):
        task_manager = get_task_manager()
        if task_manager.is_empty():
            self._l_icon.setText("")
        else:
            self._l_icon.setText((">" * self.__icon_anim_state).ljust(10, "."))
            self.__icon_anim_state = (self.__icon_anim_state + 1) % 11

    @pyqtSlot()
    def __update_timer_timeout(self):
        task_manager = get_task_manager()
        if task_manager.is_empty():
            self._l_message.setText(
                "実行中のタスクはありません"
            )
            color = "black"
            background_color = "none"
        else:
            self._l_message.setText(
                f"実行中のタスク: {task_manager.count_active()}/{task_manager.count()}"
            )
            color = "white"
            background_color = "#cc3300"
        # noinspection PyUnresolvedReferences
        self.setStyleSheet(
            "QLabel {"
            f"  color: {color};"
            f"  background-color: {background_color};"
            "   border-radius: 4px;"
            "   padding: 2px;"
            "}"
        )
