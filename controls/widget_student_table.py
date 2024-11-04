from collections import defaultdict
from contextlib import contextmanager
from functools import cache
from typing import Any, Callable, Iterable

from PyQt5.QtCore import *
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import *

from app_logging import create_logger
from application.dependency.usecases import get_student_list_id_usecase, \
    get_student_table_get_student_id_cell_data_usecase, \
    get_student_table_get_student_name_cell_data_usecase, \
    get_student_table_get_student_stage_state_cell_data_usecase, \
    get_student_table_get_student_error_cell_data_usecase, \
    get_student_dynamic_take_diff_snapshot_usecase, get_student_mark_get_usecase
from controls.mixin_shift_horizontal_scroll import HorizontalScrollWithShiftAndWheelMixin
from controls.res.fonts import font
from domain.models.stages import BuildStage, CompileStage, ExecuteStage, TestStage
from domain.models.values import StudentID
from usecases.dto.student_stage_result_diff_snapshot import StudentStageResultDiffSnapshot, \
    StudentStageResultDiff
from usecases.dto.student_table_cell_data import StudentStageStateCellDataStageState


class StudentTableColumns:
    COL_STUDENT_ID = 0
    COL_NAME = 1
    COL_MARK_RESULT = 2
    COL_STAGE_BUILD = 3
    COL_STAGE_COMPILE = 4
    COL_STAGE_EXECUTE = 5
    COL_STAGE_TEST = 6
    COL_ERROR = 7
    HEADER = (
        "学籍番号",
        "名前",
        "採点",
        "(1)ソースコード抽出",
        "(2)コンパイル",
        "(3)実行",
        "(4)テスト",
        "エラー",
    )


QtRoleType = int


def data_provider(*, column: int):
    def decorator(f: Callable[[StudentID, QtRoleType], Any]):
        setattr(f, "_cell_provider_column", column)
        return f

    return decorator


class AbstractStudentTableModelDataProvider:
    def __init__(self, student_ids: list[StudentID]):
        self._student_ids = student_ids

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


class StudentTableModelDataProvider(AbstractStudentTableModelDataProvider):
    _logger = create_logger()

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
        if role == Qt.DisplayRole:
            cell_data = get_student_table_get_student_id_cell_data_usecase().execute(student_id)
            return cell_data.student_number
        elif role == Qt.FontRole:
            cell_data = get_student_table_get_student_id_cell_data_usecase().execute(student_id)
            if cell_data.is_submission_folder_link_alive:
                return self._font_link_text()
            else:
                return self._font_dead_link_text()
        elif role == Qt.ForegroundRole:
            cell_data = get_student_table_get_student_id_cell_data_usecase().execute(student_id)
            if cell_data.is_submission_folder_link_alive:
                return self._foreground_link_text()
            else:
                return self._foreground_dead_link_text()

    @data_provider(
        column=StudentTableColumns.COL_NAME,
    )
    def get_data_of_student_name_cell(self, student_id: StudentID, role: QtRoleType):
        if role == Qt.DisplayRole:
            cell_data = get_student_table_get_student_name_cell_data_usecase().execute(student_id)
            return cell_data.student_name

    _STAGE_STATE_TEXT_MAPPING = {
        StudentStageStateCellDataStageState.UNFINISHED: "―",
        StudentStageStateCellDataStageState.FINISHED_SUCCESS: "✔",
        StudentStageStateCellDataStageState.FINISHED_FAILURE: "⚠",
    }

    @data_provider(
        column=StudentTableColumns.COL_STAGE_BUILD,
    )
    def get_data_of_stage_build_cell(self, student_id: StudentID, role: QtRoleType):
        if role == Qt.DisplayRole:
            cell_data = get_student_table_get_student_stage_state_cell_data_usecase().execute(
                student_id=student_id,
                stage_type=BuildStage,
            )
            for target_state, text in self._STAGE_STATE_TEXT_MAPPING.items():
                if all(state == target_state for state in cell_data.states.values()):
                    return text
            return "？"

    @data_provider(
        column=StudentTableColumns.COL_STAGE_COMPILE,
    )
    def get_data_of_stage_compile_cell(self, student_id: StudentID, role: QtRoleType):
        if role == Qt.DisplayRole:
            cell_data = get_student_table_get_student_stage_state_cell_data_usecase().execute(
                student_id=student_id,
                stage_type=CompileStage,
            )
            for target_state, text in self._STAGE_STATE_TEXT_MAPPING.items():
                if all(state == target_state for state in cell_data.states.values()):
                    return text
            return "？"

    @data_provider(
        column=StudentTableColumns.COL_STAGE_EXECUTE,
    )
    def get_data_of_stage_execute_cell(self, student_id: StudentID, role: QtRoleType):
        if role == Qt.DisplayRole:
            cell_data = get_student_table_get_student_stage_state_cell_data_usecase().execute(
                student_id=student_id,
                stage_type=ExecuteStage,
            )
            return " ".join(
                self._STAGE_STATE_TEXT_MAPPING[state]
                for state in cell_data.states.values()
            )

    @data_provider(
        column=StudentTableColumns.COL_STAGE_TEST,
    )
    def get_data_of_stage_test_cell(self, student_id: StudentID, role: QtRoleType):
        if role == Qt.DisplayRole:
            cell_data = get_student_table_get_student_stage_state_cell_data_usecase().execute(
                student_id=student_id,
                stage_type=TestStage,
            )
            return " ".join(
                self._STAGE_STATE_TEXT_MAPPING[state]
                for state in cell_data.states.values()
            )

    @data_provider(
        column=StudentTableColumns.COL_ERROR,
    )
    def get_data_of_error_cell(self, student_id: StudentID, role: QtRoleType):
        if role == Qt.DisplayRole:
            cell_data = get_student_table_get_student_error_cell_data_usecase().execute(
                student_id=student_id,
            )
            aggregated_text_entries = cell_data.aggregate_text_entries()
            if len(aggregated_text_entries) == 0:
                return ""
            elif len(aggregated_text_entries) == 1:
                return aggregated_text_entries[0].summary_text
            else:
                return aggregated_text_entries[0].summary_text \
                    + f"（他{len(aggregated_text_entries) - 1}件のエラー）"
        elif role == Qt.ToolTipRole:
            cell_data = get_student_table_get_student_error_cell_data_usecase().execute(
                student_id=student_id,
            )
            aggregated_text_entries = cell_data.aggregate_text_entries()
            if len(aggregated_text_entries) == 0:
                return ""
            else:
                return "\n".join(
                    f"◆ {entry.detailed_text}"
                    for entry in aggregated_text_entries
                )

    @data_provider(
        column=StudentTableColumns.COL_MARK_RESULT,
    )
    def get_data_of_mark_result_cell(self, student_id: StudentID, role: QtRoleType):
        if role == Qt.DisplayRole:
            student_mark = get_student_mark_get_usecase().execute(
                student_id=student_id,
            )
            if student_mark.is_marked:
                return str(student_mark.score)
            else:
                return "未採点"
        elif role == Qt.FontRole:
            return self._font_link_text()
        elif role == Qt.ForegroundRole:
            return self._foreground_link_text()


class CachedStudentTableModelDataProvider(AbstractStudentTableModelDataProvider):
    __CACHE_VALUE_UNSET = object()

    def __init__(
            self,
            *,
            student_ids: list[StudentID],
            provider: AbstractStudentTableModelDataProvider,
    ):
        super().__init__(student_ids)
        self._provider = provider

        self._lock = QMutex()
        self._cache: dict[int, dict[tuple[int, QtRoleType], Any]] \
            = defaultdict(lambda: defaultdict(lambda: self.__CACHE_VALUE_UNSET))
        # self._cache: row, (column, role) -> value

    @contextmanager
    def __lock(self):
        self._lock.lock()
        try:
            yield
        finally:
            self._lock.unlock()

    @classmethod
    def from_provider(cls, provider: AbstractStudentTableModelDataProvider):
        return cls(
            student_ids=provider._student_ids,
            provider=provider,
        )

    def invalidate_cache(self, row: int):
        with self.__lock():
            if row in self._cache:
                del self._cache[row]

    def get_data(self, row: int, column: int, role: QtRoleType):
        with self.__lock():
            if self._cache[row][(column, role)] is self.__CACHE_VALUE_UNSET:
                self._cache[row][(column, role)] = self._provider.get_data(row, column, role)
            return self._cache[row][(column, role)]


class StudentTableModel(QAbstractTableModel):
    def __init__(
            self,
            parent: QObject = None,
            *,
            data_provider: AbstractStudentTableModelDataProvider,
    ):
        super().__init__(parent)

        self._student_ids: list[StudentID] = data_provider._student_ids
        self._data_provider = data_provider

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
            self.__student_id_cyclic_iterator(get_student_list_id_usecase().execute())
        )

        self._timer = QTimer(self)
        self._timer.setInterval(20)
        self._timer.timeout.connect(self._on_timer_timeout)  # type: ignore
        self._timer.start()

        self._student_id_mtime_mapping: dict[StudentID, StudentStageResultDiffSnapshot] = {}
        self._current_student_index = 0

    @pyqtSlot()
    def _on_timer_timeout(self):
        # 学籍番号の取得
        student_id = next(self._student_id_iter)

        # スナップショットを取得
        new_snapshot = get_student_dynamic_take_diff_snapshot_usecase().execute(student_id)

        # 初めて巡回したとき以外は更新を確認してシグナルを送出
        if student_id in self._student_id_mtime_mapping:
            old_snapshot = self._student_id_mtime_mapping.get(student_id)
            diff = StudentStageResultDiff.from_snapshots(
                old_snapshot=old_snapshot,
                new_snapshot=new_snapshot,
            )
            if diff.updated:
                # noinspection PyUnresolvedReferences
                self.student_modified.emit(student_id)

        self._student_id_mtime_mapping[student_id] = new_snapshot


class StudentTableWidget(QTableView, HorizontalScrollWithShiftAndWheelMixin):
    _logger = create_logger()

    student_id_cell_double_clicked = pyqtSignal(StudentID, name="student_id_cell_double_clicked")
    mark_result_cell_double_clicked = pyqtSignal(StudentID, name="mark_result_cell_double_clicked")

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        # noinspection PyTypeChecker
        self._student_observer = _StudentObserver(self)
        # noinspection PyUnresolvedReferences
        self._student_observer.student_modified.connect(self._on_student_modification_observed)

        self._model_data_provider = CachedStudentTableModelDataProvider.from_provider(
            provider=StudentTableModelDataProvider(
                student_ids=get_student_list_id_usecase().execute(),
            ),
        )
        self._model = StudentTableModel(
            self,
            data_provider=self._model_data_provider,
        )  # type: ignore
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

    def __init_signals(self):
        self.doubleClicked.connect(self._on_cell_double_clicked)  # type: ignore

    @pyqtSlot()
    def _on_cell_double_clicked(self):
        if len(self.selectedIndexes()) != 1:
            return

        i_row, i_col = self.currentIndex().row(), self.currentIndex().column()
        if i_col == StudentTableColumns.COL_STUDENT_ID:
            self.student_id_cell_double_clicked.emit(self._model.get_student_id_of_row(i_row))
        elif i_col == StudentTableColumns.COL_MARK_RESULT:
            self.mark_result_cell_double_clicked.emit(self._model.get_student_id_of_row(i_row))

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
        self._model_data_provider.invalidate_cache(i_row)
        index_begin = self._model.createIndex(i_row, 0)
        index_end = self._model.createIndex(i_row, self._model.columnCount() - 1)
        self.dataChanged(index_begin, index_end)
