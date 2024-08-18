from PyQt5.QtCore import pyqtSignal, QObject, Qt, QSize
from PyQt5.QtWidgets import QToolBar, QAction

from icons import icon


class ToolBar(QToolBar):
    triggered = pyqtSignal(str)  # type: ignore

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()

    def _init_ui(self):
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.setIconSize(QSize(25, 25))

        # ツールバーアクションの追加

        a = QAction(icon("play"), "実行", self)
        a.setObjectName("run")
        self.addAction(a)

        a = QAction(icon("delete"), "クリア", self)
        a.setObjectName("clear")
        self.addAction(a)

        a = QAction(icon("vs"), "設定", self)
        a.setObjectName("settings")
        self.addAction(a)

        a = QAction(icon("testing"), "テストケースの編集", self)
        a.setObjectName("edit-testcases")
        self.addAction(a)

        a = QAction(icon("mark"), "採点", self)
        a.setObjectName("mark")
        self.addAction(a)

        a = QAction(icon("export-scores"), "点数をエクスポート", self)
        a.setObjectName("export-scores")
        self.addAction(a)

        self.actionTriggered.connect(self.__triggered)  # type: ignore

    def __triggered(self, a):
        # noinspection PyUnresolvedReferences
        self.triggered.emit(a.objectName())
