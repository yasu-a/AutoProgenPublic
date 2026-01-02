from PyQt5.QtCore import *
from PyQt5.QtGui import QShowEvent, QIcon
from PyQt5.QtWidgets import *

from feature.projman.handler.interface import IProjectOpenDialogView, IProjectOpenDialogHandler
from feature.projman.view.dto import NewProjectConfig
from shared.domain.value.identifier import ProjectID


class ProjectOpenDialog(QDialog, IProjectOpenDialogView):
    """
    Level 3: Container (ウィンドウ)
    プロジェクトを開く/作成するダイアログ
    """

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._handler: IProjectOpenDialogHandler | None = None
        self._result: ProjectID | NewProjectConfig | None = None

        self._init_ui()

    def set_handler(self, handler: IProjectOpenDialogHandler) -> None:
        """Handlerを注入（DI）"""
        self._handler = handler

    def _init_ui(self):
        self.setWindowTitle("WELCOME")
        self.setModal(True)
        self.resize(800, 400)

        layout_root = QVBoxLayout()
        self.setLayout(layout_root)

        self._container = QTabWidget(self)
        layout_root.addWidget(self._container)

        # タブを左横にする
        self._container.setTabPosition(QTabWidget.West)

        # シグナル接続
        # noinspection PyUnresolvedReferences
        self.finished.connect(self.__finished)

    def add_tab(self, widget: QWidget, title: str, icon: QIcon = None) -> int:
        """
        外部からタブを追加できるようにする（Composition）
        Handlerは独立して生成され、後から追加される
        """
        index = self._container.addTab(widget, "")
        # アイコンとラベルの設定
        if icon:
            self._container.tabBar().setTabIcon(index, icon)

        # ラベルを設定（左側に配置）
        label = QLabel(title, self)
        self._container.tabBar().setTabButton(
            index,
            QTabBar.LeftSide,
            label,
        )
        return index

    def showEvent(self, evt: QShowEvent) -> None:
        """ダイアログ表示時にHandlerに通知"""
        super().showEvent(evt)
        self._handler.on_view_initialized()

    # noinspection PyMethodOverriding
    @pyqtSlot()
    def __finished(self):
        """ダイアログが閉じられたとき"""
        pass  # 必要に応じてクリーンアップ処理を追加

    # ===== IProjectOpenDialogView実装 =====
    def switch_to_create_tab(self) -> None:
        """タブ1（新規作成）に切り替え"""
        self._container.setCurrentIndex(0)

    def switch_to_list_tab(self) -> None:
        """タブ2（一覧）に切り替え"""
        self._container.setCurrentIndex(1)

    def get_result(self) -> NewProjectConfig | ProjectID | None:
        """ダイアログの結果を取得"""
        return self._result

    def set_result(self, result: NewProjectConfig | ProjectID) -> None:
        """ダイアログの結果を設定"""
        self._result = result
        self.accept()
