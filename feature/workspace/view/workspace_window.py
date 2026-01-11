from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from feature.workspace.handler.interface import IWorkspaceWindowView, IWorkspaceWindowHandler, \
    IProcessResourceUsageStatusBarView
from feature.workspace.view.widget_status_process_resource_usage import \
    ProcessResourceUsageStatusBarWidget
from feature.workspace.view.widget_status_task_state import TaskStateStatusBarWidget
from feature.workspace.view.widget_status_unstable_version_notif import \
    UnstableVersionNotificationStatusBarWidget
from feature.workspace.view.widget_toolbar import ToolBar
from util.app_logging import create_logger


class WorkspaceWindow(QMainWindow, IWorkspaceWindowView):
    """
    ワークスペースウィンドウ（メイン画面）
    Handlerパターンを使用してロジックを分離
    """
    # Navigatorに「閉じた」と伝えるシグナル
    # noinspection PyArgumentList
    closed = pyqtSignal()

    _logger = create_logger()

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._handler: IWorkspaceWindowHandler

        self._init_ui()

    def set_handler(self, handler: IWorkspaceWindowHandler) -> None:
        """Handlerを注入（DI）"""
        # noinspection PyAttributeOutsideInit
        self._handler = handler
        # Handlerに初期化を通知
        self._handler.on_view_initialized()

    def _init_ui(self):
        self.resize(1500, 800)

        # ツールバー
        self._tool_bar = ToolBar(self)
        # noinspection PyUnresolvedReferences
        self.addToolBar(self._tool_bar)

        # 生徒のテーブル
        self._w_student_table: QWidget

        # ステータスバー
        #  - タスクモニタ
        # noinspection PyTypeChecker
        self._sb_task_state = TaskStateStatusBarWidget(self)
        # noinspection PyUnresolvedReferences
        self.statusBar().addPermanentWidget(self._sb_task_state)
        # noinspection PyUnresolvedReferences
        self.statusBar().addPermanentWidget(QLabel(self), 1)
        #  - テスト版通知
        # noinspection PyTypeChecker
        self._sb_unstable_version_notif = UnstableVersionNotificationStatusBarWidget(self)
        # noinspection PyUnresolvedReferences
        self.statusBar().addPermanentWidget(self._sb_unstable_version_notif)
        #  - リソースモニタ
        # noinspection PyTypeChecker
        self._sb_process_resource_usage = ProcessResourceUsageStatusBarWidget(self)
        # noinspection PyUnresolvedReferences
        self.statusBar().addPermanentWidget(self._sb_process_resource_usage)

        # シグナル接続
        self._tool_bar.triggered.connect(self.__tool_bar_triggered)

    @pyqtSlot(str)
    def __tool_bar_triggered(self, name: str):
        """ツールバーのアクションがトリガーされたとき"""
        self._handler.on_toolbar_action_triggered(name)

    def closeEvent(self, evt, **kwargs):
        """ウィンドウが閉じられたとき"""
        self._handler.on_view_closed()

        # 閉じる処理の前にシグナルを送る
        self.closed.emit()

        # タスク停止処理はNavigatorで行うため、ここでは削除

        super().closeEvent(evt)

    # ===== IWorkspaceWindowView実装 =====

    def add_table(self, table_view: QWidget) -> None:
        # noinspection PyAttributeOutsideInit
        self._w_student_table = table_view
        # noinspection PyUnresolvedReferences
        self.setCentralWidget(self._w_student_table)

    def set_window_title(self, title: str) -> None:
        """ウィンドウタイトルを設定"""
        # noinspection PyUnresolvedReferences
        self.setWindowTitle(title)

    def get_parent_widget(self):
        """親ウィジェットを取得（ダイアログの親として使用）"""
        return self

    def get_process_resource_usage_status_bar_view(self) -> IProcessResourceUsageStatusBarView:
        """リソース使用状況ステータスバーのViewを取得"""
        return self._sb_process_resource_usage
