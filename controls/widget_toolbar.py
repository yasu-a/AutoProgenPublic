from PyQt5.QtCore import pyqtSignal, QObject, Qt, QSize
from PyQt5.QtWidgets import QToolBar, QAction

from controls.res.icons import icon


class ToolBar(QToolBar):
    triggered = pyqtSignal(str)  # type: ignore

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()

    def _init_ui(self):
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.setIconSize(QSize(25, 25))

        # ツールバーアクションの追加

        self._a_run = QAction(icon("play"), "実行", self)
        self._a_run.setObjectName("run")
        self._a_run.setEnabled(False)
        self.addAction(self._a_run)

        self._a_stop = QAction(icon("stop"), "中断", self)
        self._a_stop.setObjectName("stop")
        self._a_stop.setEnabled(False)
        self.addAction(self._a_stop)

        self._a_delete = QAction(icon("delete"), "クリア", self)
        self._a_delete.setObjectName("clear")
        self._a_delete.setEnabled(False)
        self.addAction(self._a_delete)

        self._a_settings = QAction(icon("vs"), "設定", self)
        self._a_settings.setObjectName("edit-settings")
        self._a_settings.setEnabled(False)
        self.addAction(self._a_settings)

        self._a_edit_testcases = QAction(icon("testing"), "テストケースの編集", self)
        self._a_edit_testcases.setObjectName("edit-testcases")
        self._a_edit_testcases.setEnabled(False)
        self.addAction(self._a_edit_testcases)

        self._a_mark = QAction(icon("mark"), "採点", self)
        self._a_mark.setObjectName("mark")
        self._a_mark.setEnabled(False)
        self.addAction(self._a_mark)

        self._a_export_scores = QAction(icon("export-scores"), "点数をエクスポート", self)
        self._a_export_scores.setObjectName("export-scores")
        self._a_export_scores.setEnabled(False)
        self.addAction(self._a_export_scores)

        self.actionTriggered.connect(self.__triggered)  # type: ignore

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
