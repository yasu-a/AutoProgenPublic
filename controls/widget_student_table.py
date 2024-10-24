from datetime import datetime
from functools import cache
from typing import Any, Callable, Iterable

from PyQt5.QtCore import *
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import *

from app_logging import create_logger
from application.dependency.services import get_student_progress_check_timestamp_query_service
from application.dependency.usecases import get_student_id_list_usecase, \
    get_student_submission_folder_show_usecase, get_student_table_get_student_id_cell_data_usecase, \
    get_student_table_get_student_name_cell_data_usecase, \
    get_student_table_get_student_stage_state_cell_data_use_case, \
    get_student_table_get_student_error_cell_data_use_case
from controls.mixin_shift_horizontal_scroll import HorizontalScrollWithShiftAndWheelMixin
from domain.models.stages import BuildStage, CompileStage, ExecuteStage, TestStage
from domain.models.values import StudentID
from fonts import font
from usecases.dto.student_table_cell_data import StudentStageStateCellDataStageState


class StudentTableColumns:
    COL_STUDENT_ID = 0
    COL_NAME = 1
    COL_STAGE_BUILD = 2
    COL_STAGE_COMPILE = 3
    COL_STAGE_EXECUTE = 4
    COL_STAGE_TEST = 5
    COL_ERROR = 6
    COL_TESTCASE_RESULT = 7
    COL_MARK_RESULT = 8
    HEADER = (
        "学籍番号",
        "名前",
        "実行環境構築",
        "コンパイル",
        "実行",
        "テスト",
        "エラー",
        "テスト結果",
        "採点結果",
    )


QtRoleType = int


def data_provider(*, column: int):
    def decorator(f: Callable[[StudentID, QtRoleType], Any]):
        setattr(f, "_cell_provider_column", column)
        return f

    return decorator


class StudentTableModelDataProvider:
    def __init__(self, student_ids: list[StudentID]):
        self._student_ids = student_ids
        # self._progress_service = get_progress_service()  TODO: CHECK UNUSED METHODS AND REMOVE ME
        self._logger = create_logger(name=f"{type(self).__name__}")

    @classmethod
    @cache
    def _font_link_text(cls) -> QFont:
        f = font(monospace=True)
        f.setUnderline(True)
        return f

    @classmethod
    @cache
    def _font_dead_link_text(cls) -> QFont:
        f = font(monospace=True)
        return f

    @classmethod
    @cache
    def _foreground_link_text(cls) -> QColor:
        return QColor("blue")

    @classmethod
    @cache
    def _foreground_dead_link_text(cls) -> QColor:
        return QColor("red").darker()

    @data_provider(
        column=StudentTableColumns.COL_STUDENT_ID,
    )
    def get_data_of_student_id_cell(self, student_id: StudentID, role: QtRoleType):
        cell_data = get_student_table_get_student_id_cell_data_usecase().execute(student_id)
        if role == Qt.DisplayRole:
            return cell_data.student_number
        elif role == Qt.FontRole:
            if cell_data.is_submission_folder_link_alive:
                return self._font_link_text()
            else:
                return self._font_dead_link_text()
        elif role == Qt.ForegroundRole:
            if cell_data.is_submission_folder_link_alive:
                return self._foreground_link_text()
            else:
                return self._foreground_dead_link_text()

    @data_provider(
        column=StudentTableColumns.COL_NAME,
    )
    def get_data_of_student_name_cell(self, student_id: StudentID, role: QtRoleType):
        cell_data = get_student_table_get_student_name_cell_data_usecase().execute(student_id)
        if role == Qt.DisplayRole:
            return cell_data.student_name

    _STAGE_STATE_TEXT_MAPPING = {
        StudentStageStateCellDataStageState.UNFINISHED: "  ",
        StudentStageStateCellDataStageState.FINISHED_SUCCESS: "✔",
        StudentStageStateCellDataStageState.FINISHED_FAILURE: "☠",
    }

    @data_provider(
        column=StudentTableColumns.COL_STAGE_BUILD,
    )
    def get_data_of_stage_build_cell(self, student_id: StudentID, role: QtRoleType):
        if role == Qt.DisplayRole:
            cell_data = get_student_table_get_student_stage_state_cell_data_use_case().execute(
                student_id=student_id,
                stage_type=BuildStage,
            )
            return "/".join(
                self._STAGE_STATE_TEXT_MAPPING[state]
                for state in cell_data.states.values()
            )

    @data_provider(
        column=StudentTableColumns.COL_STAGE_COMPILE,
    )
    def get_data_of_stage_compile_cell(self, student_id: StudentID, role: QtRoleType):
        if role == Qt.DisplayRole:
            cell_data = get_student_table_get_student_stage_state_cell_data_use_case().execute(
                student_id=student_id,
                stage_type=CompileStage,
            )
            return "/".join(
                self._STAGE_STATE_TEXT_MAPPING[state]
                for state in cell_data.states.values()
            )

    @data_provider(
        column=StudentTableColumns.COL_STAGE_EXECUTE,
    )
    def get_display_stage_execute_cell(self, student_id: StudentID, role: QtRoleType):
        if role == Qt.DisplayRole:
            cell_data = get_student_table_get_student_stage_state_cell_data_use_case().execute(
                student_id=student_id,
                stage_type=ExecuteStage,
            )
            return "/".join(
                self._STAGE_STATE_TEXT_MAPPING[state]
                for state in cell_data.states.values()
            )

    @data_provider(
        column=StudentTableColumns.COL_STAGE_TEST,
    )
    def get_display_stage_test_cell(self, student_id: StudentID, role: QtRoleType):
        if role == Qt.DisplayRole:
            cell_data = get_student_table_get_student_stage_state_cell_data_use_case().execute(
                student_id=student_id,
                stage_type=TestStage,
            )
            return "/".join(
                self._STAGE_STATE_TEXT_MAPPING[state]
                for state in cell_data.states.values()
            )

    @data_provider(
        column=StudentTableColumns.COL_ERROR,
    )
    def get_display_role_of_error(self, student_id: StudentID, role: QtRoleType):
        cell_data = get_student_table_get_student_error_cell_data_use_case().execute(
            student_id=student_id,
        )
        if role == Qt.DisplayRole:
            if len(cell_data.text_entries) == 0:
                return ""
            elif len(cell_data.text_entries) == 1:
                return cell_data.text_entries[0].summary_text
            else:
                return cell_data.text_entries[0].summary_text \
                    + f" 他{len(cell_data.text_entries) - 1}件のエラー"
        elif role == Qt.ToolTipRole:
            if len(cell_data.text_entries) == 0:
                return ""
            else:
                return "\n".join(
                    entry.summary_text
                    for entry in cell_data.text_entries
                )

    @data_provider(
        column=StudentTableColumns.COL_TESTCASE_RESULT,
    )
    def get_display_role_of_testcase_result(self, student_id: StudentID, role: QtRoleType):
        _ = student_id
        _ = role
        return None

    @data_provider(
        column=StudentTableColumns.COL_MARK_RESULT,
    )
    def get_display_role_of_mark_result(self, student_id: StudentID, role: QtRoleType):
        _ = student_id
        _ = role
        return None

    def _find_cell_provider(self, column: int):
        for name in dir(self):
            obj = getattr(self, name)
            if callable(obj) and hasattr(obj, "_cell_provider_column"):
                provider = obj
                provider_column = getattr(obj, "_cell_provider_column")
                if provider_column == column:
                    return provider
        raise ValueError(f"Provider for {column=} not defined")

    def get_data(self, row: int, column: int, role: QtRoleType):
        provider = self._find_cell_provider(column)
        if provider is not None:
            return provider(student_id=self._student_ids[row], role=role)
        else:
            return None


class StudentTableModel(QAbstractTableModel):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._student_ids: list[StudentID] = get_student_id_list_usecase().execute()

        self._data_provider = StudentTableModelDataProvider(
            student_ids=self._student_ids,
        )

    def get_row_of_student(self, student_id: StudentID) -> int:
        return self._student_ids.index(student_id)

    COLS_STATE = (
        StudentTableColumns.COL_STAGE_BUILD,
        StudentTableColumns.COL_STAGE_COMPILE,
        StudentTableColumns.COL_STAGE_EXECUTE,
    )

    # noinspection PyMethodOverriding
    def data(self, index: QModelIndex, role: int) -> Any:
        i_row, i_col = index.row(), index.column()
        return self._data_provider.get_data(
            row=i_row,
            column=i_col,
            role=role,
        )

    # noinspection PyMethodOverriding
    def rowCount(self, parent=QModelIndex()) -> int:
        # with state.data(readonly=True) as data:
        #     return len(data.students)
        return len(self._student_ids)

    # noinspection PyMethodOverriding
    def columnCount(self, parent=QModelIndex()) -> int:
        return len(StudentTableColumns.HEADER)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return StudentTableColumns.HEADER[section]
            else:
                return ""

    def get_student_id_of_row(self, i_row: int) -> StudentID:
        return self._student_ids[i_row]


class _StudentObserver(QObject):
    student_modified = pyqtSignal(StudentID, name="student_modified")

    @staticmethod
    def __student_id_cyclic_iterator(student_ids: list[StudentID]) -> Iterable[StudentID]:
        while True:
            for student_id in student_ids:
                yield student_id

    def __init__(self, parent: QObject):
        super().__init__(parent)

        self._student_id_iter = iter(
            self.__student_id_cyclic_iterator(get_student_id_list_usecase().execute())
        )

        self._timer = QTimer(self)
        self._timer.setInterval(5)
        self._timer.timeout.connect(self._on_timer_timeout)  # type: ignore
        self._timer.start()

        self._student_id_mtime_mapping: dict[StudentID, datetime | None] = {}
        self._current_student_index = 0

    @pyqtSlot()
    def _on_timer_timeout(self):
        student_id = next(self._student_id_iter)
        prev_mtime = self._student_id_mtime_mapping.get(student_id)
        current_mtime = get_student_progress_check_timestamp_query_service().execute(student_id)
        if prev_mtime != current_mtime:
            if prev_mtime is not None:  # 初めて巡回したときは更新を行わない
                # noinspection PyUnresolvedReferences
                self.student_modified.emit(student_id)
        self._student_id_mtime_mapping[student_id] = current_mtime


class StudentTableWidget(QTableView, HorizontalScrollWithShiftAndWheelMixin):
    _logger = create_logger()

    # selection_changed = pyqtSignal(str)  # type: ignore  # student_id

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        # noinspection PyTypeChecker
        self._student_observer = _StudentObserver(self)
        # noinspection PyUnresolvedReferences
        self._student_observer.student_modified.connect(self._on_student_modification_observed)

        self._model = StudentTableModel(self)  # type: ignore
        self.setModel(self._model)

        self._init_ui()
        self.__init_signals()

    def _init_ui(self):
        # self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setDefaultSectionSize(100)
        self.verticalHeader().hide()

        vh = self.verticalHeader()
        vh.setSectionResizeMode(QHeaderView.Fixed)
        vh.setDefaultSectionSize(20)

        self.setColumnWidth(StudentTableColumns.COL_STUDENT_ID, 150)
        self.setColumnWidth(StudentTableColumns.COL_NAME, 150)
        self.setColumnWidth(StudentTableColumns.COL_ERROR, 400)
        self.setColumnWidth(StudentTableColumns.COL_TESTCASE_RESULT, 300)
        self.setColumnWidth(StudentTableColumns.COL_MARK_RESULT, 300)

    def __init_signals(self):
        self.doubleClicked.connect(self._on_cell_double_clicked)  # type: ignore

    @pyqtSlot()
    def _on_cell_double_clicked(self):
        if len(self.selectedIndexes()) != 1:
            return

        i_row, i_col = self.currentIndex().row(), self.currentIndex().column()
        if i_col == StudentTableColumns.COL_STUDENT_ID:
            get_student_submission_folder_show_usecase().execute(
                student_id=self._model.get_student_id_of_row(i_row),
            )

        # if self.currentIndex().column() == StudentTableModel.COL_STUDENT_ID:
        #     index = self.currentIndex().row()
        #     with state.data(readonly=True) as data:
        #         student_id = data.student_ids[index]
        #     state.project_service.open_submission_folder_in_explorer(student_id)
        # elif self.currentIndex().column() == StudentTableModel.COL_MARK_RESULT:
        #     index = self.currentIndex().row()
        #     with state.data(readonly=True) as data:
        #         student_id = data.student_ids[index]
        #     dialog = StudentMarkDialog(self, student_id_filter=[student_id])
        #     dialog.exec_()

    @pyqtSlot(StudentID)
    def _on_student_modification_observed(self, student_id):
        i_row = self._model.get_row_of_student(student_id)
        self._logger.debug(f"Updating row {i_row} {student_id}")
        index_begin = self._model.createIndex(i_row, 0)
        index_end = self._model.createIndex(i_row, self._model.columnCount() - 1)
        self.dataChanged(index_begin, index_end)
