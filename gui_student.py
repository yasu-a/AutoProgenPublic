from typing import Any

from PyQt5.QtCore import *
from PyQt5.QtGui import QColor, QWheelEvent
from PyQt5.QtWidgets import *

import state
from app_logging import create_logger
from fonts import font
from models.student import StudentProcessStage, StudentProcessResult


class StudentTableModel(QAbstractTableModel):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

    HEADER = "学籍番号", "名前", "実行環境構築", "コンパイル", "自動テスト", "エラー", "テスト結果"
    COL_STUDENT_ID = 0
    COL_NAME = 1
    COL_STATE_BUILD = 2
    COL_STATE_COMPILE = 3
    COL_STATE_TEST = 4
    COL_ERROR = 5
    COL_TESTCASE_RESULT = 6

    COLS_STATE = COL_STATE_BUILD, COL_STATE_COMPILE, COL_STATE_TEST

    # noinspection PyMethodOverriding
    def data(self, index: QModelIndex, role: int) -> Any:
        i_row, i_col = index.row(), index.column()

        if role == Qt.DisplayRole:
            with state.data(readonly=True) as data:
                student = data.students[data.student_ids[i_row]]

            if i_col == self.COL_STUDENT_ID:
                return f"{student.meta.student_id}"
            elif i_col == self.COL_NAME:
                return student.meta.name
            elif i_col in self.COLS_STATE:
                flags = student.process_stage_flags
                stage = {
                    self.COL_STATE_BUILD: StudentProcessStage.ENVIRONMENT_BUILDING,
                    self.COL_STATE_COMPILE: StudentProcessStage.COMPILE,
                    self.COL_STATE_TEST: StudentProcessStage.AUTO_TESTING,
                }[i_col]
                result = flags[stage]
                stage_result_text = {
                    StudentProcessResult.UNFINISHED: "",
                    StudentProcessResult.OK: "✔",
                    StudentProcessResult.ERROR: "エラー",
                }[result]
                return stage_result_text
            elif i_col == self.COL_ERROR:
                with state.data(readonly=True) as data:
                    main_error_reason \
                        = data.students[data.student_ids[i_row]].last_stage_main_error_reason
                    return "" if main_error_reason is None else str(main_error_reason)
            elif i_col == self.COL_TESTCASE_RESULT:
                if student.test_result is None:
                    return ""
                else:
                    return student.test_result.testcase_result_string

        elif role == Qt.ForegroundRole:
            with state.data(readonly=True) as data:
                student = data.students[data.student_ids[i_row]]

            if i_col == self.COL_STUDENT_ID:
                if student.meta.submission_folder_name is not None:
                    return QColor("blue")
            if i_col in self.COLS_STATE:
                if "エラー" in self.data(index, role=Qt.DisplayRole):
                    return QColor("red")

        elif role == Qt.FontRole:
            with state.data(readonly=True) as data:
                student = data.students[data.student_ids[i_row]]

            monospace = i_col == self.COL_STUDENT_ID or i_col == self.COL_TESTCASE_RESULT
            cell_font = font(monospace=monospace)
            if i_col == self.COL_STUDENT_ID:
                if student.meta.submission_folder_name is not None:
                    cell_font.setUnderline(True)
                    cell_font.setBold(True)
            if i_col in self.COLS_STATE:
                if "エラー" in self.data(index, role=Qt.DisplayRole):
                    cell_font.setBold(True)
            return cell_font

        elif role == Qt.ToolTipRole:
            return self.data(index, Qt.DisplayRole)

    # noinspection PyMethodOverriding
    def rowCount(self, parent=QModelIndex()) -> int:
        with state.data(readonly=True) as data:
            return len(data.students)

    # noinspection PyMethodOverriding
    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.HEADER)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.HEADER[section]
            else:
                return ""


class StudentTableWidget(QTableView):
    _logger = create_logger()

    selection_changed = pyqtSignal(str)  # type: ignore  # student_id

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._model = StudentTableModel(self)  # type: ignore
        self.setModel(self._model)

        self.__init_ui()
        self.__init_signals()

        self._update_timer = QTimer(self)
        self._update_timer.setInterval(100)
        self._update_timer.timeout.connect(self.__update_data_on_timeout)  # type: ignore
        self._update_timer.start()
        self.__last_modify_count = -1

    def __init_ui(self):
        # self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setDefaultSectionSize(100)
        self.verticalHeader().hide()

        vh = self.verticalHeader()
        vh.setSectionResizeMode(QHeaderView.Fixed)
        vh.setDefaultSectionSize(20)

        self.setColumnWidth(0, 150)
        self.setColumnWidth(1, 150)
        self.setColumnWidth(5, 400)
        self.setColumnWidth(6, 300)

    def __init_signals(self):
        self.clicked.connect(self.__w_list_selection_changed)  # type: ignore
        self.doubleClicked.connect(self.open_selected_in_explorer)  # type: ignore

    def __w_list_selection_changed(self):
        index = self.currentIndex().row()
        with state.data(readonly=True) as data:
            student_id = data.student_ids[index]
        self.selection_changed.emit(student_id)  # type: ignore

    @pyqtSlot()
    def open_selected_in_explorer(self):
        if len(self.selectedIndexes()) != 1:
            return
        if self.currentIndex().column() != 0:
            return
        index = self.currentIndex().row()
        with state.data(readonly=True) as data:
            student_id = data.student_ids[index]
        state.project_service.open_submission_folder_in_explorer(student_id)

    def __update_data_on_timeout(self):
        current_modify_count = state.data_manager.modify_count
        if current_modify_count != self.__last_modify_count:
            self.__last_modify_count = current_modify_count
            # model = self.model()
            # index_begin = model.index(0, 0)
            # index_end = model.index(model.rowCount() - 1, model.columnCount() - 1)
            self.dataChanged(QModelIndex(), QModelIndex())
            self._logger.info("updated")

    # https://stackoverflow.com/questions/38234021/horizontal-scroll-on-wheelevent-with-shift-too-fast
    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() == Qt.ShiftModifier:
            scrollbar = self.horizontalScrollBar()
        else:
            scrollbar = self.verticalScrollBar()

        action = QAbstractSlider.SliderSingleStepAdd
        if event.angleDelta().y() > 0:
            action = QAbstractSlider.SliderSingleStepSub

        for _ in range(6):
            scrollbar.triggerAction(action)


# class StudentInfoDetailWidget(QWidget):
#     def __init__(self, parent: QObject = None):
#         super().__init__(parent)
#
#         self.__init_ui()
#
#     def __init_ui(self):
#         layout = QGridLayout()
#
#         self._w_tree = QTreeWidget(self)
#         # self._w_tree.setFont()  set the font on the model to change it
#         # self._w_tree.setHeaderHidden(True)
#         self._w_tree.setHeaderLabels(["", ""])  # type: ignore
#         layout.addWidget(self._w_tree)
#
#         self.setLayout(layout)
#
#     @pyqtSlot(str)
#     def update_info(self, student_id: str):
#         return
#
#         self._w_tree.clear()
#         self._w_tree.setColumnCount(2)
#         self._w_tree.setColumnWidth(0, 200)
#
#         self._w_tree.addTopLevelItem(QTreeWidgetItem(["学籍番号", info["student_id"]]))
#         self._w_tree.addTopLevelItem(
#             QTreeWidgetItem(["状態", "取り込み失敗" if info["fail"] else "取り込み成功"]))
#         if info["reason"]:
#             self._w_tree.addTopLevelItem(QTreeWidgetItem(["理由", info["reason"]]))
#         self._w_tree.addTopLevelItem(QTreeWidgetItem(["レポートフォルダ", info["report_dir_path"]]))
#         if info["report_zip_path"] is not None:
#             self._w_tree.addTopLevelItem(QTreeWidgetItem(["zipファイル", info["report_zip_path"]]))
#         if info["env_dir_path"] is not None:
#             self._w_tree.addTopLevelItem(QTreeWidgetItem(["実行フォルダ", info["env_dir_path"]]))
#         item_build_result = QTreeWidgetItem(["実行フォルダ構築結果"])
#         item_build_result_ok = QTreeWidgetItem(["取り込みに成功したファイル"])
#         if info["env_build_result"] is not None:
#             for src_filename, result in info["env_build_result"].items():
#                 if result["status"] == "ok":
#                     item_build_result_ok.addChild(QTreeWidgetItem([src_filename]))
#             item_build_result.addChild(item_build_result_ok)
#             item_build_result_error = QTreeWidgetItem(["取り込みに失敗したファイル"])
#             for src_filename, result in info["env_build_result"].items():
#                 if result["status"] != "ok":
#                     item_build_result_error.addChild(
#                         QTreeWidgetItem([result["reason"], src_filename]))
#             item_build_result.addChild(item_build_result_error)
#             self._w_tree.addTopLevelItem(item_build_result)
#             self._w_tree.expandItem(item_build_result)
#             self._w_tree.expandItem(item_build_result_ok)
#             self._w_tree.expandItem(item_build_result_error)
#         if info["env_meta"] is not None:
#             item_env_meta = QTreeWidgetItem(["取り込んだファイル"])
#             for dst_filename, result in info["env_meta"].items():
#                 item_env_meta_entry = QTreeWidgetItem([dst_filename, result["label"]])
#                 item_env_meta_entry.addChild(QTreeWidgetItem(["種別", result["label"]]))
#                 item_env_meta_entry.addChild(
#                     QTreeWidgetItem(["展開日時", str(datetime.fromtimestamp(result["updated"]))]))
#                 item_env_meta.addChild(item_env_meta_entry)
#             self._w_tree.addTopLevelItem(item_env_meta)
#             self._w_tree.expandItem(item_env_meta)


class StudentInfoWidget(QWidget):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self.__project_path = None

        self.__init_ui()
        self.__init_signals()

    def __init_ui(self):
        layout = QHBoxLayout()
        self.setLayout(layout)

        splitter = QSplitter(self)
        splitter.setOrientation(Qt.Vertical)
        layout.addWidget(splitter)

        if "splitter-top":
            w_top = QWidget(self)
            splitter.addWidget(w_top)

            layout_top = QVBoxLayout()
            w_top.setLayout(layout_top)

            self._w_student_table = StudentTableWidget()
            layout_top.addWidget(self._w_student_table)

        # if "splitter-bottom":
        #     self._w_student_info_detail = StudentInfoDetailWidget()
        #     splitter.addWidget(self._w_student_info_detail)

        # self._b_next_error = QPushButton(self, text="次のエラー", minimumWidth=150)
        # self._b_next_error.clicked.connect(self._w_student_info_list.select_next_error)
        # layout_ctrl.addWidget(self._b_next_error)

    def __init_signals(self):
        self._w_student_table.selection_changed.connect(  # type: ignore
            self.__list_selection_changed
        )
        # self._b_rebuild_env.clicked.connect(  # type: ignore
        #     self.rebuild_env
        # )

    @pyqtSlot(str)
    def __list_selection_changed(self, student_id):
        # self._w_student_info_detail.update_info(student_id)
        pass
