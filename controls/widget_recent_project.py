import time
from collections import deque
from contextlib import contextmanager

from PyQt5.QtCore import *
from PyQt5.QtGui import QCursor, QMouseEvent
from PyQt5.QtWidgets import *

from application.dependency.usecases import get_project_list_recent_summary_usecase, \
    get_project_base_folder_show_usecase, get_project_folder_show_usecase, \
    get_project_delete_usecase, get_project_get_size_query_usecase
from controls.dialog_progress import AbstractProgressDialogWorker, AbstractProgressDialog
from controls.widget_clickable_label import ClickableLabelWidget
from domain.models.values import ProjectID
from res.fonts import get_font
from res.icons import get_icon
from usecases.dto.project_summary import ProjectSummary


class RecentProjectListItemWidget(QWidget):
    # ----------------------------------------------
    #  Project-X                              [...]
    #  report5.zip       Q.5 2024/11/05 30MB
    # ----------------------------------------------

    control_triggered = pyqtSignal(ProjectID, name="control_triggered")
    selected = pyqtSignal(ProjectID, name="project_selected")

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._project_summary: ProjectSummary | None = None

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
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

                self._l_project_name = ClickableLabelWidget(self)
                self._l_project_name.setMinimumWidth(200)
                f = get_font(underline=True, bold=True, large=True)
                self._l_project_name.setFont(f)
                layout_top.addWidget(self._l_project_name)

                layout_top.addStretch(1)

            if "bottom":
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

        if "right":
            layout_right = QHBoxLayout()
            layout_right.setContentsMargins(20, 0, 20, 0)
            layout.addLayout(layout_right)

            # self._b_open = QPushButton(self)
            # self._b_open.setIcon(icon("folder"))
            # self._b_open.setFixedWidth(30)
            # self._b_open.setFixedHeight(30)
            # self._b_open.setEnabled(False)
            # layout_right.addWidget(self._b_open)

            self._b_actions = QPushButton(self)
            self._b_actions.setIcon(get_icon("cog"))
            self._b_actions.setFixedWidth(30)
            self._b_actions.setFixedHeight(30)
            self._b_actions.setEnabled(False)
            layout_right.addWidget(self._b_actions)

    def _init_signals(self):
        # noinspection PyUnresolvedReferences
        self._b_actions.clicked.connect(self.__b_actions_clicked)
        # noinspection PyUnresolvedReferences
        self._l_project_name.clicked.connect(self.__l_project_name_clicked)
        # # noinspection PyUnresolvedReferences
        # self._b_open.clicked.connect(self.__b_open_clicked)

    @pyqtSlot()
    def __b_actions_clicked(self):
        if self._project_summary is None:
            return
        self.control_triggered.emit(self._project_summary.project_id)

    @pyqtSlot()
    def __l_project_name_clicked(self):
        if self._project_summary is None:
            return
        self.selected.emit(self._project_summary.project_id)

    # @pyqtSlot()
    # def __b_open_clicked(self):
    #     if self._project_summary is None:
    #         return
    #     self.selected.emit(self._project_summary.project_id)

    def set_data(self, project_summary: ProjectSummary | None):
        if project_summary is None:
            self._l_project_name.setText("")
            self._l_open_at.setText("")
            self._l_zip_name.setText("")
            self._l_target_number.setText("")
            self._l_size.setText("")
            self._b_actions.setEnabled(False)
            # self._b_open.setEnabled(False)
            self._l_project_name.unsetCursor()
        else:
            self._l_project_name.setText(project_summary.project_name)
            self._l_open_at.setText(project_summary.open_at.strftime("%Y/%m/%d %H:%M:%S"))
            self._l_zip_name.setText(project_summary.zip_name)
            self._l_target_number.setText(f"設問 {project_summary.target_number!s}")
            self._l_size.setText("--")
            self._b_actions.setEnabled(True)
            # self._b_open.setEnabled(True)
            self._l_project_name.setCursor(QCursor(Qt.PointingHandCursor))
        self._project_summary = project_summary

    def set_size_field(self, size: int) -> int:
        self._l_size.setText(f"{size // (1 << 20):,}MB")
        return size

    def is_size_unset(self) -> bool:
        return self._l_size.text() == "--"

    def get_data(self) -> ProjectSummary | None:
        return self._project_summary


class RecentProjectListWidget(QListWidget):
    project_selected = pyqtSignal(ProjectID, name="project_selected")
    open_project_triggered = pyqtSignal(ProjectID, name="action_triggered")
    delete_project_triggered = pyqtSignal(ProjectID, name="delete_project_triggered")
    show_project_triggered = pyqtSignal(ProjectID, name="show_project_project_triggered")

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        pass

    def _init_signals(self):
        pass

    def __insert_item(self, i: int, project_summary: ProjectSummary):
        # 項目のウィジェットを初期化
        # noinspection PyTypeChecker
        item_widget = RecentProjectListItemWidget(self)
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
        item_widget.control_triggered.connect(self.__item_widget_control_triggered)
        item_widget.selected.connect(self.__item_widget_selected)

    @pyqtSlot(ProjectID)
    def __item_widget_control_triggered(self, project_id: ProjectID):
        menu = QMenu(self)

        # メニューにアクションを追加
        a_open = QAction("開く", self)
        # noinspection PyUnresolvedReferences
        a_open.triggered.connect(lambda: self.open_project_triggered.emit(project_id))
        menu.addAction(a_open)

        a_show = QAction("場所をエクスプローラで開く", self)
        # noinspection PyUnresolvedReferences
        a_show.triggered.connect(lambda: self.show_project_triggered.emit(project_id))
        menu.addAction(a_show)

        a_delete = QAction("削除", self)
        # noinspection PyUnresolvedReferences
        a_delete.triggered.connect(lambda: self.delete_project_triggered.emit(project_id))
        menu.addAction(a_delete)

        # メニューを表示
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        # コンテキストメニューをボタンの下に表示
        position = QCursor.pos()
        menu.exec_(position)

    @pyqtSlot(ProjectID)
    def __item_widget_selected(self, project_id: ProjectID):
        self.project_selected.emit(project_id)

    def mouseDoubleClickEvent(self, evt: QMouseEvent):
        index = self.indexAt(evt.pos())
        if not index.isValid():
            return

        item = self.item(index.row())
        item_w = self.itemWidget(item)
        assert isinstance(item_w, RecentProjectListItemWidget)
        project_id = item_w.get_data().project_id
        self.project_selected.emit(project_id)

    def set_data(self, project_summary_lst: list[ProjectSummary]) -> None:
        self.clear()
        for i, project_summary in enumerate(project_summary_lst):
            self.__insert_item(i, project_summary)

    def set_size_field(self, project_id: ProjectID, size: int) -> None:
        for i in range(self.count()):
            item = self.item(i)
            item_w = self.itemWidget(item)
            assert isinstance(item_w, RecentProjectListItemWidget)
            if item_w.get_data().project_id == project_id:
                item_w.set_size_field(size)


class _RecentProjectSizeFieldGetWorker(QThread):
    field_acquired = pyqtSignal(ProjectID, int, name="field_acquired")  # project_id and size

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self.__stop = False
        self._lock = QMutex()
        self._q: deque[ProjectID] = deque()

    @contextmanager
    def __lock(self):
        self._lock.lock()
        try:
            yield
        finally:
            self._lock.unlock()

    def stop(self) -> None:
        self.__stop = True

    def clear_queue(self) -> None:
        with self.__lock():
            self._q.clear()

    def set_queue(self, project_ids: list[ProjectID]) -> None:
        with self.__lock():
            self._q.extend(project_ids)

    def run(self):
        while True:
            if self.__stop:
                break
            with self.__lock():
                if not self._q:
                    time.sleep(1)
                    continue
                project_id = self._q.popleft()
            size = get_project_get_size_query_usecase().execute(
                project_id=project_id,
            )
            self.field_acquired.emit(project_id, size)
            time.sleep(0.05)


class _ProjectDeleteWorker(AbstractProgressDialogWorker):
    def __init__(self, parent: QObject = None, *, project_id: ProjectID):
        super().__init__(parent)

        self._project_delete_usecase = get_project_delete_usecase()
        self._project_id = project_id

    def run(self):
        self._callback("プロジェクトを削除しています・・・")
        self._project_delete_usecase.execute(self._project_id)
        time.sleep(0.5)  # プロジェクトのサイズが小さいとUIが一瞬で消えるので少し待つ


class ProjectDeleteProgressDialog(AbstractProgressDialog):
    # プロジェクトを削除しそのプログレスを表示するダイアログ

    def __init__(self, parent: QObject = None, *, project_id: ProjectID):
        super().__init__(
            parent,
            title="プロジェクトの削除",
            worker_producer=lambda: _ProjectDeleteWorker(
                self,
                project_id=project_id,
            ),
        )


class RecentProjectWidget(QWidget):
    # noinspection PyArgumentList
    accepted = pyqtSignal(ProjectID)

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._project_size_field_get_worker = _RecentProjectSizeFieldGetWorker()

        self._init_ui()
        self._init_signals()

        self.__update_list()

    def _init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        self._w_list = RecentProjectListWidget()
        self._w_list.project_selected.connect(self.__project_selected)
        layout.addWidget(self._w_list)

        layout_button = QHBoxLayout()
        layout.addLayout(layout_button)

        self._b_open_folder = QPushButton(self)
        self._b_open_folder.setText("プロジェクトの管理フォルダを開く")
        # noinspection PyUnresolvedReferences
        self._b_open_folder.clicked.connect(self.__b_open_folder_clicked)
        layout_button.addWidget(self._b_open_folder)

        layout_button.addStretch(1)

    def _init_signals(self):
        self._w_list.open_project_triggered.connect(self.__project_selected)
        self._w_list.delete_project_triggered.connect(self.__delete_project_triggered)
        self._w_list.show_project_triggered.connect(self.__show_project_triggered)
        self._project_size_field_get_worker.field_acquired.connect(
            self.__project_size_field_get_worker_size_field_acquired
        )

    def __update_list(self) -> None:
        # プロジェクトのリストを読み込んで設定する
        project_summary_lst = get_project_list_recent_summary_usecase().execute()
        self._w_list.set_data(project_summary_lst)
        # サイズ取得のスレッドにキューを追加する
        self._project_size_field_get_worker.clear_queue()
        self._project_size_field_get_worker.set_queue([
            project_summary.project_id
            for project_summary in project_summary_lst
            if project_summary.project_id is not None
        ])

    @pyqtSlot()
    def __b_open_folder_clicked(self):
        get_project_base_folder_show_usecase().execute()

    @pyqtSlot(ProjectID)
    def __project_selected(self, project_id: ProjectID):
        self.accepted.emit(project_id)

    @pyqtSlot(ProjectID)
    def __delete_project_triggered(self, project_id: ProjectID):
        # noinspection PyTypeChecker
        if QMessageBox.warning(
                self,
                "プロジェクトの削除",
                f"プロジェクト{project_id!s}を削除しますか？\nこの操作は元に戻せません。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
        ) == QMessageBox.No:
            return
        ProjectDeleteProgressDialog(project_id=project_id).exec_()
        self.__update_list()

    @pyqtSlot(ProjectID)
    def __show_project_triggered(self, project_id: ProjectID):
        get_project_folder_show_usecase().execute(project_id)

    @pyqtSlot(ProjectID, int)
    def __project_size_field_get_worker_size_field_acquired(self, project_id: ProjectID, size: int):
        self._w_list.set_size_field(project_id, size)

    # TODO: スレッドを開始するもっといい実装方法を探す
    def start_worker(self) -> None:
        self._project_size_field_get_worker.start()

    # TODO: スレッドを終了するもっといい実装方法を探す
    def stop_worker(self) -> None:
        self._project_size_field_get_worker.stop()
        self._project_size_field_get_worker.wait()
