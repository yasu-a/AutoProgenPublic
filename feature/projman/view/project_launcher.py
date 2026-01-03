from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtGui import QShowEvent, QIcon
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget, QLabel, QTabBar

from feature.projman.handler.interface import IProjectLauncherView, IProjectLauncherHandler


class ProjectLauncherDialog(QMainWindow, IProjectLauncherView):
    """
    プロジェクト起動/作成を行うランチャー画面
    """

    # Navigatorに「閉じた」と伝えるシグナル
    closed = pyqtSignal()

    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self._handler: IProjectLauncherHandler

        self._init_ui()

    def set_handler(self, handler: IProjectLauncherHandler) -> None:
        """Handlerを注入（DI）"""
        # noinspection PyAttributeOutsideInit
        self._handler = handler

    def _init_ui(self):
        self.setWindowTitle("AutoProgen - Welcome")
        self.resize(800, 450)

        # 中央ウィジェット
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # タブウィジェット
        self._tab_widget = QTabWidget(self)
        self._tab_widget.setTabPosition(QTabWidget.West)  # 左側にタブを配置
        layout.addWidget(self._tab_widget)

    def showEvent(self, evt: QShowEvent) -> None:
        """表示時にHandlerに通知"""
        super().showEvent(evt)
        self._handler.on_view_initialized()

    def closeEvent(self, evt, **kwargs):
        """閉じるときにシグナルを発火"""
        # noinspection PyUnresolvedReferences
        self.closed.emit()
        super().closeEvent(evt)

    # ===== IProjectLauncherView実装 =====

    def add_tab(self, widget: QWidget, title: str, icon: QIcon = None) -> None:
        """タブを追加"""
        index = self._tab_widget.addTab(widget, "")

        if icon:
            self._tab_widget.tabBar().setTabIcon(index, icon)

        # タブのテキストをラベルとして設定（アイコンの横などに配置調整される）
        label = QLabel(title, self)
        self._tab_widget.tabBar().setTabButton(
            index,
            QTabBar.LeftSide,
            label,
        )

    def switch_to_create_tab(self) -> None:
        """作成タブへ切り替え"""
        self._tab_widget.setCurrentIndex(0)

    def switch_to_list_tab(self) -> None:
        """一覧タブへ切り替え"""
        self._tab_widget.setCurrentIndex(1)

    def get_parent_widget(self):
        return self
