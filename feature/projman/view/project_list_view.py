from typing import List, Union

from PyQt5.QtCore import *
from PyQt5.QtGui import QCursor, QShowEvent
from PyQt5.QtWidgets import *

from feature.projman.handler.interface import IProjectListView, IProjectListHandler
from feature.projman.usecase.dto import NormalProjectSummary, AbstractProjectSummary, \
    ErrorProjectSummary
from shared.view.style.font import get_font
from shared.view.style.icon import get_icon
from shared.domain.value.identifier import ProjectID
from shared.view.widget_clickable_label import ClickableLabel


class ProjectListItemView(QWidget):
    # ------------------------------------------------------
    #  ProjectEntity-X                              [...]
    #  report5.zip       Q.5 2024/11/05 30MB
    #  <error message>
    # ------------------------------------------------------

    open_project_requested = pyqtSignal(ProjectID, name="open_project_requested")
    open_folder_requested = pyqtSignal(ProjectID, name="open_folder_requested")
    delete_project_requested = pyqtSignal(ProjectID, name="delete_project_requested")

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._project_summary: AbstractProjectSummary | None = None

        self._init_ui()

    def _init_ui(self):
        self.installEventFilter(self)

        layout = QHBoxLayout()
        self.setLayout(layout)

        if "left":
            layout_left = QVBoxLayout()
            layout_left.setContentsMargins(0, 0, 0, 0)
            layout_left.setSpacing(0)
            layout.addLayout(layout_left)

            if "top":
                layout_top = QHBoxLayout()
                layout_left.addLayout(layout_top)

                self._l_project_name = ClickableLabel(self)
                self._l_project_name.setMinimumWidth(200)
                f = get_font(underline=True, bold=True, large=True)
                self._l_project_name.setFont(f)
                layout_top.addWidget(self._l_project_name)

                layout_top.addStretch(1)

            if "middle":
                layout_bottom = QHBoxLayout()
                layout_left.addLayout(layout_bottom)

                self._l_zip_name = QLabel(self)
                self._l_zip_name.setMinimumWidth(200)
                layout_bottom.addWidget(self._l_zip_name)

                self._l_target_number = QLabel(self)
                self._l_target_number.setFixedWidth(50)
                layout_bottom.addWidget(self._l_target_number)

                self._l_open_at = QLabel(self)
                self._l_open_at.setFixedWidth(150)
                layout_bottom.addWidget(self._l_open_at)

                self._l_size = QLabel(self)
                self._l_size.setFixedWidth(50)
                layout_bottom.addWidget(self._l_size)

            if "bottom":
                self._l_error_message = QLabel(self)
                self._l_error_message.setStyleSheet("color: red")  # type: ignore
                layout_left.addWidget(self._l_error_message)

        if "right":
            layout_right = QHBoxLayout()
            layout_right.setContentsMargins(20, 0, 20, 0)
            layout.addLayout(layout_right)

            self._b_actions = QPushButton(self)
            self._b_actions.setIcon(get_icon("cog"))
            self._b_actions.setFixedWidth(30)
            self._b_actions.setFixedHeight(30)
            self._b_actions.setEnabled(False)
            layout_right.addWidget(self._b_actions)

        # シグナル接続
        # noinspection PyUnresolvedReferences
        self._b_actions.clicked.connect(self.__b_actions_clicked)
        # noinspection PyUnresolvedReferences
        self._l_project_name.clicked.connect(self.__l_project_name_clicked)

    @pyqtSlot()
    def __b_actions_clicked(self):
        if self._project_summary is None:
            return

        menu = QMenu(self)

        # メニューにアクションを追加

        if not self._project_summary.has_error:
            a_open = QAction("開く", self)
            # noinspection PyUnresolvedReferences
            a_open.triggered.connect(
                lambda: self.open_project_requested.emit(self._project_summary.project_id),
            )
            menu.addAction(a_open)

        a_show = QAction("場所をエクスプローラで開く", self)
        # noinspection PyUnresolvedReferences
        a_show.triggered.connect(
            lambda: self.open_folder_requested.emit(self._project_summary.project_id),
        )
        menu.addAction(a_show)

        a_delete = QAction("削除", self)
        # noinspection PyUnresolvedReferences
        a_delete.triggered.connect(
            lambda: self.delete_project_requested.emit(self._project_summary.project_id),
        )
        menu.addAction(a_delete)

        # メニューを表示
        # noinspection PyTypeChecker
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        menu.exec_(QCursor.pos())  # コンテキストメニューをボタンの下に表示

    @pyqtSlot()
    def __l_project_name_clicked(self):
        if self._project_summary is None:
            return
        if self._project_summary.has_error:
            return
        self.open_project_requested.emit(self._project_summary.project_id)

    def eventFilter(self, target: QObject, event: QEvent):
        if event.type() == QEvent.MouseButtonDblClick:
            self.__l_project_name_clicked()
            return True
        return False

    def set_data(self, project_summary: AbstractProjectSummary | None):
        if project_summary is None:
            self._l_project_name.setText("")
            self._l_open_at.setText("")
            self._l_zip_name.setText("")
            self._l_target_number.setText("")
            self._l_size.setText("")
            self._b_actions.setEnabled(False)
            self._l_project_name.unsetCursor()
            self._l_error_message.hide()
        elif project_summary.has_error:
            assert isinstance(project_summary, ErrorProjectSummary), project_summary
            self._l_project_name.setText(project_summary.project_name)
            self._l_open_at.setText("--")
            self._l_zip_name.setText("--")
            self._l_target_number.setText("--")
            self._l_size.setText("--")
            self._b_actions.setEnabled(True)
            self._l_project_name.setCursor(QCursor(Qt.ForbiddenCursor))
            self._l_error_message.show()  # type: ignore
            self._l_error_message.setText(project_summary.error_message)
        else:
            assert isinstance(project_summary, NormalProjectSummary), project_summary
            self._l_project_name.setText(project_summary.project_name)
            self._l_open_at.setText(project_summary.open_at.strftime("%Y/%m/%d %H:%M:%S"))
            self._l_zip_name.setText(project_summary.zip_name)
            self._l_target_number.setText(f"設問 {project_summary.target_number!s}")
            self._l_size.setText("--")
            self._b_actions.setEnabled(True)
            self._l_project_name.setCursor(QCursor(Qt.PointingHandCursor))
            self._l_error_message.hide()
        self._project_summary = project_summary

    def set_size_field(self, size: int) -> int:
        self._l_size.setText(f"{size // (1 << 20):,}MB")
        return size

    def is_size_unset(self) -> bool:
        return self._l_size.text() == "--"

    def get_data(self) -> AbstractProjectSummary | None:
        return self._project_summary


class ProjectListWidget(QListWidget):
    open_project_requested = pyqtSignal(ProjectID, name="open_project_requested")
    open_folder_requested = pyqtSignal(ProjectID, name="open_folder_requested")
    delete_project_requested = pyqtSignal(ProjectID, name="delete_project_requested")

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()

    def _init_ui(self):
        pass

    # noinspection DuplicatedCode
    def __insert_item(self, i: int, project_summary: AbstractProjectSummary):
        # 項目のウィジェットを初期化
        # noinspection PyTypeChecker
        item_widget = ProjectListItemView(self)
        item_widget.set_data(project_summary)
        # Qtのリスト項目を初期化
        list_item = QListWidgetItem()
        # noinspection PyUnresolvedReferences
        list_item.setSizeHint(item_widget.sizeHint())
        list_item.setFlags(list_item.flags() & ~Qt.ItemIsSelectable)
        # リストに追加
        self.insertItem(i, list_item)
        # 項目のウィジェットとQtのリスト項目を関連付ける
        # noinspection PyUnresolvedReferences
        self.setItemWidget(list_item, item_widget)
        # シグナルをつなげる
        # noinspection PyUnresolvedReferences
        item_widget.open_project_requested.connect(self.open_project_requested)
        item_widget.open_folder_requested.connect(self.open_folder_requested)
        item_widget.delete_project_requested.connect(self.delete_project_requested)

    def set_data(self, project_summary_lst: List[
        Union[NormalProjectSummary, ErrorProjectSummary]]) -> None:
        self.clear()
        for i, project_summary in enumerate(project_summary_lst):
            self.__insert_item(i, project_summary)

    def set_size_field(self, project_id: ProjectID, size: int) -> None:
        for i in range(self.count()):
            item = self.item(i)
            item_w = self.itemWidget(item)
            assert isinstance(item_w, ProjectListItemView)
            if item_w.get_data() and item_w.get_data().project_id == project_id:
                item_w.set_size_field(size)


class ProjectListView(QWidget, IProjectListView):
    # noinspection PyArgumentList
    project_opened = pyqtSignal(ProjectID, name="project_opened")
    settings_requested = pyqtSignal(name="settings_requested")

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._handler: IProjectListHandler

        self._init_ui()
        # 注意: ここでは__update_list()を呼ばない（showEventでHandlerが呼ぶ）

    def set_handler(self, handler: IProjectListHandler) -> None:
        """Handlerを注入（DI）"""
        self._handler = handler

    def _init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        self._w_list = ProjectListWidget()
        layout.addWidget(self._w_list)

        layout_button = QHBoxLayout()
        layout.addLayout(layout_button)

        self._b_open_projects_base_folder = QPushButton(self)
        self._b_open_projects_base_folder.setText("プロジェクトの管理フォルダを開く")
        layout_button.addWidget(self._b_open_projects_base_folder)

        layout_button.addStretch(1)

        # 設定ボタンを追加
        self._b_setting = QPushButton(self)
        self._b_setting.setIcon(get_icon("settings"))
        self._b_setting.setText("設定")
        layout_button.addWidget(self._b_setting)

        # シグナル接続
        self._w_list.open_project_requested.connect(
            self.__w_list_open_project_requested,
        )
        self._w_list.open_folder_requested.connect(
            self.__w_list_open_folder_requested,
        )
        self._w_list.delete_project_requested.connect(
            self.__w_list_delete_project_requested,
        )
        # noinspection PyUnresolvedReferences
        self._b_open_projects_base_folder.clicked.connect(
            self.__b_open_projects_base_folder_clicked,
        )
        # noinspection PyUnresolvedReferences
        self._b_setting.clicked.connect(
            self.__b_settings_clicked,
        )

    def showEvent(self, evt: QShowEvent) -> None:
        """タブがアクティブになったときに自動ロード"""
        super().showEvent(evt)
        self._handler.on_view_initialized()

    def hideEvent(self, evt) -> None:
        """タブが非アクティブになったときにWorkerを停止"""
        super().hideEvent(evt)
        self._handler.stop_size_loading()

    @pyqtSlot(ProjectID)
    def __w_list_open_project_requested(self, project_id: ProjectID):
        """プロジェクトを開く要求 → Handlerに通知"""
        self._handler.on_open_project_requested(project_id)
        # 外部（Dialog）に通知
        self.project_opened.emit(project_id)

    @pyqtSlot(ProjectID)
    def __w_list_open_folder_requested(self, project_id: ProjectID):
        """プロジェクトフォルダを開く要求 → Handlerに通知"""
        self._handler.on_open_folder_requested(project_id)

    @pyqtSlot(ProjectID)
    def __w_list_delete_project_requested(self, project_id: ProjectID):
        """プロジェクト削除要求 → Handlerに通知"""
        self._handler.on_delete_project_requested(project_id)

    @pyqtSlot()
    def __b_open_projects_base_folder_clicked(self):
        """プロジェクト管理フォルダを開く要求 → Handlerに通知"""
        self._handler.on_open_base_folder_requested()

    @pyqtSlot()
    def __b_settings_clicked(self):
        """設定ボタンがクリックされたとき → シグナルを発火"""
        # noinspection PyUnresolvedReferences
        self.settings_requested.emit()

    # ===== IProjectListView実装 =====
    def update_project_list(
            self,
            projects: List[Union[NormalProjectSummary, ErrorProjectSummary]]
    ) -> None:
        """Handlerから呼ばれる：プロジェクトリストを更新"""
        self._w_list.set_data(projects)
        # Handlerにサイズキューを設定してもらう（インターフェースに追加が必要かも）
        project_ids = [
            p.project_id for p in projects
            if not p.has_error and p.project_id is not None
        ]
        self._handler.set_size_queue(project_ids)

    def update_project_size(self, project_id: ProjectID, size: int) -> None:
        """Handlerから呼ばれる：プロジェクトサイズを更新"""
        self._w_list.set_size_field(project_id, size)

    def show_delete_confirmation(self, project_id: ProjectID) -> bool:
        """Handlerから呼ばれる：削除確認ダイアログ"""
        result = QMessageBox.warning(
            self,
            "プロジェクトの削除",
            f"プロジェクト{project_id!s}を削除しますか？\nこの操作は元に戻せません。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return result == QMessageBox.Yes

    def show_error_message(self, message: str) -> None:
        """Handlerから呼ばれる：エラーメッセージを表示"""
        QMessageBox.critical(self, "エラー", message)

    def start_size_loading(self) -> None:
        """Handlerから呼ばれる：サイズ取得の開始"""
        pass  # HandlerがWorkerを管理するため、ここでは何もしない

    def stop_size_loading(self) -> None:
        """Handlerから呼ばれる：サイズ取得の終了"""
        pass  # HandlerがWorkerを管理するため、ここでは何もしない
