from PyQt5.QtCore import pyqtSignal, QObject, Qt, QSize, QTimer, pyqtSlot
from PyQt5.QtWidgets import QToolBar, QAction

from application.dependency.tasks import get_task_manager
from controls.res.icons import get_icon


class ToolBar(QToolBar):
    triggered = pyqtSignal(str)  # type: ignore

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self.__state_update_timer = QTimer(self)
        self.__state_update_timer.setInterval(1000)

        self._init_ui()
        self._init_signals()

        self.__state_update_timer.start()

    def _init_ui(self):
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.setIconSize(QSize(15, 15))

        # ツールバーアクションの追加

        self._a_open_project = QAction(get_icon("folder"), "プロジェクトを開く", self)
        self._a_open_project.setObjectName("open-project")
        self._a_open_project.setEnabled(True)
        self.addAction(self._a_open_project)

        self._a_settings = QAction(get_icon("settings"), "設定", self)
        self._a_settings.setObjectName("edit-settings")
        self._a_settings.setEnabled(False)
        self.addAction(self._a_settings)

        self.addSeparator()

        self._a_edit_testcases = QAction(get_icon("research"), "テストケースの編集", self)
        self._a_edit_testcases.setObjectName("edit-testcases")
        self._a_edit_testcases.setEnabled(False)
        self.addAction(self._a_edit_testcases)

        self.addSeparator()

        self._a_run = QAction(get_icon("play"), "実行", self)
        self._a_run.setObjectName("run")
        self._a_run.setEnabled(False)
        self.addAction(self._a_run)

        self._a_stop = QAction(get_icon("stop"), "中断", self)
        self._a_stop.setObjectName("stop")
        self._a_stop.setEnabled(False)
        self.addAction(self._a_stop)

        self._a_delete = QAction(get_icon("trash"), "クリア", self)
        self._a_delete.setObjectName("clear")
        self._a_delete.setEnabled(False)
        self.addAction(self._a_delete)

        self.addSeparator()

        self._a_mark = QAction(get_icon("marker"), "採点", self)
        self._a_mark.setObjectName("mark")
        self._a_mark.setEnabled(False)
        self.addAction(self._a_mark)

        self._a_export_scores = QAction(get_icon("write"), "点数をエクスポート", self)
        self._a_export_scores.setObjectName("export-scores")
        self._a_export_scores.setEnabled(False)
        self.addAction(self._a_export_scores)

        self.addSeparator()

        self._a_about = QAction(get_icon("fountain-pen"), "About", self)
        self._a_about.setObjectName("about")
        self.addAction(self._a_about)

    def _init_signals(self):
        # noinspection PyUnresolvedReferences
        self.actionTriggered.connect(self.__triggered)
        # noinspection PyUnresolvedReferences
        self.__state_update_timer.timeout.connect(self.__state_update_timer_timeout)

    def __triggered(self, a):
        # noinspection PyUnresolvedReferences
        self.triggered.emit(a.objectName())

    def update_button_state(self, is_task_alive: bool):
        if is_task_alive:
            self._a_run.setEnabled(False)
            self._a_stop.setEnabled(True)
            self._a_delete.setEnabled(False)
            self._a_settings.setEnabled(False)
            self._a_edit_testcases.setEnabled(False)
            self._a_mark.setEnabled(False)
            self._a_export_scores.setEnabled(False)
        else:
            self._a_run.setEnabled(True)
            self._a_stop.setEnabled(False)
            self._a_delete.setEnabled(True)
            self._a_settings.setEnabled(True)
            self._a_edit_testcases.setEnabled(True)
            self._a_mark.setEnabled(True)
            self._a_export_scores.setEnabled(True)

    @pyqtSlot()
    def __state_update_timer_timeout(self):
        self.update_button_state(is_task_alive=not get_task_manager().is_empty())
