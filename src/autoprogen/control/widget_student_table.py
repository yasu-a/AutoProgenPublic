from collections import defaultdict
from contextlib import contextmanager
from functools import cache
from typing import Any, Callable

from PyQt5.QtCore import *
from PyQt5.QtGui import QColor, QFont, QMouseEvent
from PyQt5.QtWidgets import *

from autoprogen.control.mixin_shift_horizontal_scroll import HorizontalScrollWithShiftAndWheelMixin
from autoprogen.control.qt_student_change_bridge import QtStudentChangeBridge
from autoprogen.domain.model.stage import AbstractStage, BuildStage, CompileStage, ExecuteStage, TestStage
from autoprogen.domain.model.student_mark import StudentMark
from autoprogen.domain.model.value import StudentID
from autoprogen.res.font import get_font
from autoprogen.service.student_change_event_bus import StudentChangeEventBus
from autoprogen.usecase.dto.student_table_cell_data import (
    StudentErrorCellData,
    StudentIDCellData,
    StudentNameCellData,
    StudentStageStateCellData,
    StudentStageStateCellDataStageState,
)
from autoprogen.usecase.student_table_load import StudentTableLoadUseCase, StudentTableRowSnapshot
from autoprogen.util.app_logging import create_logger


class StudentTableColumns:
    COL_STUDENT_ID = 0
    COL_NAME = 1
    COL_SCORE = 2
    COL_STAGE_BUILD = 3
    COL_STAGE_COMPILE = 4
    COL_STAGE_EXECUTE = 5
    COL_STAGE_TEST = 6
    COL_ERROR = 7
    HEADER = (
        "学籍番号",
        "名前",
        "点数",
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

    @property
    def student_ids(self) -> list[StudentID]:
        return self._student_ids

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

    def __init__(
            self,
            *,
            student_ids: list[StudentID],
    ):
        super().__init__(student_ids)
        self._row_snapshots: dict[StudentID, StudentTableRowSnapshot] = {}

    def set_rows(self, rows: list[StudentTableRowSnapshot]) -> None:
        """全件ロード済みの表示データを設定する。"""
        self._student_ids = [row.student_id for row in rows]
        self._row_snapshots = {row.student_id: row for row in rows}

    def replace_row(self, row: StudentTableRowSnapshot) -> None:
        """既存の学生行の表示データを順序を変えずに置き換える。"""
        if row.student_id not in self._row_snapshots:
            raise KeyError(row.student_id)
        self._row_snapshots[row.student_id] = row

    def _id_cell(self, student_id: StudentID) -> StudentIDCellData:
        """ロード済みの学籍番号データを返す。"""
        return self._row_snapshots[student_id].id_cell

    def _name_cell(self, student_id: StudentID) -> StudentNameCellData:
        """ロード済みの学生名データを返す。"""
        return self._row_snapshots[student_id].name_cell

    def _stage_cell(
            self, student_id: StudentID, stage_type: type[AbstractStage]
    ) -> StudentStageStateCellData:
        """ロード済みのステージ状態を返す。"""
        return self._row_snapshots[student_id].stage_cells[stage_type]

    def _error_cell(self, student_id: StudentID) -> StudentErrorCellData:
        """ロード済みのエラーデータを返す。"""
        return self._row_snapshots[student_id].error_cell

    def _mark(self, student_id: StudentID) -> StudentMark:
        """ロード済みの採点データを返す。"""
        return self._row_snapshots[student_id].mark

    @classmethod
    @cache
    def _font_link_text(cls, *, monospace: bool) -> QFont:
        f = get_font(monospace=monospace)
        f.setUnderline(True)
        return f

    @classmethod
    @cache
    def _font_dead_link_text(cls, monospace: bool) -> QFont:
        f = get_font(monospace=monospace)
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
            cell_data = self._id_cell(student_id)
            return cell_data.student_number
        elif role == Qt.FontRole:
            cell_data = self._id_cell(student_id)
            if cell_data.is_submission_folder_link_alive:
                return self._font_link_text(monospace=True)
            else:
                return self._font_dead_link_text(monospace=True)
        elif role == Qt.ForegroundRole:
            cell_data = self._id_cell(student_id)
            if cell_data.is_submission_folder_link_alive:
                return self._foreground_link_text()
            else:
                return self._foreground_dead_link_text()
        else:
            return None

    @data_provider(
        column=StudentTableColumns.COL_NAME,
    )
    def get_data_of_student_name_cell(self, student_id: StudentID, role: QtRoleType):
        if role == Qt.DisplayRole:
            cell_data = self._name_cell(student_id)
            return cell_data.student_name
        else:
            return None

    _CHAR_UNFINISHED = "―"
    _CHAR_SUCCESS = "✔"
    _CHAR_FAILURE = "⚠"

    _STAGE_STATE_TEXT_MAPPING = {
        StudentStageStateCellDataStageState.UNFINISHED: _CHAR_UNFINISHED,
        StudentStageStateCellDataStageState.FINISHED_SUCCESS: _CHAR_SUCCESS,
        StudentStageStateCellDataStageState.FINISHED_FAILURE: _CHAR_FAILURE,
    }

    @classmethod
    def _foreground_status_text(cls, text) -> QColor | None:
        if cls._CHAR_FAILURE in text:
            return QColor("red")
        if cls._CHAR_UNFINISHED in text:
            return None
        if cls._CHAR_SUCCESS in text:
            return QColor("limegreen")
        return None

    @data_provider(
        column=StudentTableColumns.COL_STAGE_BUILD,
    )
    def get_data_of_stage_build_cell(self, student_id: StudentID, role: QtRoleType):
        if role == Qt.DisplayRole:
            cell_data = self._stage_cell(student_id, BuildStage)
            for target_state, text in self._STAGE_STATE_TEXT_MAPPING.items():
                if all(state == target_state for state in cell_data.states.values()):
                    return text
            return "？"
        elif role == Qt.ForegroundRole:
            text = self.get_data_of_stage_build_cell(student_id, Qt.DisplayRole)
            return self._foreground_status_text(text)
        else:
            return None

    @data_provider(
        column=StudentTableColumns.COL_STAGE_COMPILE,
    )
    def get_data_of_stage_compile_cell(self, student_id: StudentID, role: QtRoleType):
        if role == Qt.DisplayRole:
            cell_data = self._stage_cell(student_id, CompileStage)
            for target_state, text in self._STAGE_STATE_TEXT_MAPPING.items():
                if all(state == target_state for state in cell_data.states.values()):
                    return text
            return "？"
        elif role == Qt.ForegroundRole:
            text = self.get_data_of_stage_compile_cell(student_id, Qt.DisplayRole)
            return self._foreground_status_text(text)
        else:
            return None

    @data_provider(
        column=StudentTableColumns.COL_STAGE_EXECUTE,
    )
    def get_data_of_stage_execute_cell(self, student_id: StudentID, role: QtRoleType):
        if role == Qt.DisplayRole:
            cell_data = self._stage_cell(student_id, ExecuteStage)
            return " ".join(
                self._STAGE_STATE_TEXT_MAPPING[state]
                for state in cell_data.states.values()
            )
        elif role == Qt.ForegroundRole:
            text = self.get_data_of_stage_execute_cell(student_id, Qt.DisplayRole)
            return self._foreground_status_text(text)
        else:
            return None

    @data_provider(
        column=StudentTableColumns.COL_STAGE_TEST,
    )
    def get_data_of_stage_test_cell(self, student_id: StudentID, role: QtRoleType):
        if role == Qt.DisplayRole:
            cell_data = self._stage_cell(student_id, TestStage)
            return " ".join(
                self._STAGE_STATE_TEXT_MAPPING[state]
                for state in cell_data.states.values()
            )
        elif role == Qt.ForegroundRole:
            text = self.get_data_of_stage_test_cell(student_id, Qt.DisplayRole)
            return self._foreground_status_text(text)
        else:
            return None

    @data_provider(
        column=StudentTableColumns.COL_ERROR,
    )
    def get_data_of_error_cell(self, student_id: StudentID, role: QtRoleType):
        if role == Qt.DisplayRole:
            cell_data = self._error_cell(student_id)
            aggregated_text_entries = cell_data.aggregate_text_entries()
            if len(aggregated_text_entries) == 0:
                return ""
            elif len(aggregated_text_entries) == 1:
                return aggregated_text_entries[0].summary_text
            else:
                return aggregated_text_entries[0].summary_text \
                    + f"（他{len(aggregated_text_entries) - 1}件のエラー）"
        elif role == Qt.ToolTipRole:
            cell_data = self._error_cell(student_id)
            aggregated_text_entries = cell_data.aggregate_text_entries()
            if len(aggregated_text_entries) == 0:
                return ""
            else:
                return "\n".join(
                    f"◆ {entry.detailed_text}"
                    for entry in aggregated_text_entries
                )
        else:
            return None

    @data_provider(
        column=StudentTableColumns.COL_SCORE,
    )
    def get_data_of_mark_result_cell(self, student_id: StudentID, role: QtRoleType):
        if role == Qt.DisplayRole:
            student_mark = self._mark(student_id)
            if student_mark.is_marked:
                return str(student_mark.score)
            else:
                return "未採点"
        elif role == Qt.FontRole:
            return self._font_link_text(monospace=False)
        elif role == Qt.ForegroundRole:
            return self._foreground_link_text()
        else:
            return None


class CachedStudentTableModelDataProvider(AbstractStudentTableModelDataProvider):
    __CACHE_VALUE_UNSET = object()

    def __init__(
            self,
            *,
            student_ids: list[StudentID],
            provider: StudentTableModelDataProvider,
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
    def from_provider(cls, provider: StudentTableModelDataProvider):
        return cls(
            student_ids=provider._student_ids,
            provider=provider,
        )

    def set_rows(self, rows: list[StudentTableRowSnapshot]) -> None:
        """全行のロード結果を反映し、旧キャッシュを破棄する。"""
        with self.__lock():
            self._provider.set_rows(rows)
            self._student_ids = self._provider.student_ids
            self._cache.clear()

    def replace_row(self, row_index: int, row: StudentTableRowSnapshot) -> None:
        """学生一人のスナップショットを差し替え、該当行の表示キャッシュを消す。"""
        with self.__lock():
            if self._student_ids[row_index] != row.student_id:
                raise ValueError("更新対象の学生IDが行と一致しません")
            self._provider.replace_row(row)
            self._cache.pop(row_index, None)

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
            provider: AbstractStudentTableModelDataProvider,
    ):
        super().__init__(parent)

        self._student_ids: list[StudentID] = provider.student_ids
        self._data_provider = provider

    def get_row_of_student(self, student_id: StudentID) -> int:
        return self._student_ids.index(student_id)

    def set_rows(self, rows: list[StudentTableRowSnapshot]) -> None:
        """モデルの全行をロード結果で置き換える。"""
        self.beginResetModel()
        self._data_provider.set_rows(rows)
        self._student_ids = self._data_provider.student_ids
        self.endResetModel()

    def replace_row(self, row: StudentTableRowSnapshot) -> None:
        """現在の行位置を維持して学生一人の表示データを更新する。"""
        row_index = self.get_row_of_student(row.student_id)
        self._data_provider.replace_row(row_index, row)
        index_begin = self.index(row_index, 0)
        index_end = self.index(row_index, self.columnCount() - 1)
        self.dataChanged.emit(index_begin, index_end)

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
        else:
            return None

    def get_student_id_of_row(self, i_row: int) -> StudentID:
        return self._student_ids[i_row]


class StudentTableWidget(QTableView, HorizontalScrollWithShiftAndWheelMixin):
    _logger = create_logger()

    student_id_cell_triggered = pyqtSignal(StudentID, name="student_id_cell_triggered")
    mark_result_cell_triggered = pyqtSignal(StudentID, name="mark_result_cell_triggered")

    def __init__(
            self,
            parent: QObject = None,
            *,
            student_change_event_bus: StudentChangeEventBus,
            student_table_load_usecase: StudentTableLoadUseCase,
        ):
        super().__init__(parent)
        student_ids: list[StudentID] = []
        self._student_table_load_usecase = student_table_load_usecase

        self._student_change_bridge = QtStudentChangeBridge(
            self,
            student_ids=student_ids,
            student_change_event_bus=student_change_event_bus,
        )
        self._student_change_bridge.student_changed.connect(self._on_student_modification_observed)

        self._model_data_provider = CachedStudentTableModelDataProvider.from_provider(
            provider=StudentTableModelDataProvider(
                student_ids=student_ids,
            ),
        )

        # noinspection PyTypeChecker
        self._model = StudentTableModel(
            self,
            provider=self._model_data_provider,
        )  # type: ignore
        self.setModel(self._model)

        self._init_ui()
        self.__init_signals()

    def apply_loaded_rows(self, rows: list[StudentTableRowSnapshot]) -> None:
        """ワーカーが取得した全学生の表示データをGUIスレッドで反映する。"""
        self._model.set_rows(rows)
        self._student_change_bridge.set_student_ids([row.student_id for row in rows])

    def _init_ui(self):
        # self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setDefaultSectionSize(100)
        self.verticalHeader().hide()
        self.setMouseTracking(True)  # mouseEventを使うため

        vh = self.verticalHeader()
        vh.setSectionResizeMode(QHeaderView.Fixed)
        vh.setDefaultSectionSize(20)

        self.setColumnWidth(StudentTableColumns.COL_STUDENT_ID, 150)
        self.setColumnWidth(StudentTableColumns.COL_NAME, 150)
        self.setColumnWidth(StudentTableColumns.COL_ERROR, 400)

    def __init_signals(self):
        self.clicked.connect(self._on_cell_triggered)  # type: ignore

    @pyqtSlot()
    def _on_cell_triggered(self):
        if len(self.selectedIndexes()) != 1:
            return

        i_row, i_col = self.currentIndex().row(), self.currentIndex().column()
        if i_col == StudentTableColumns.COL_STUDENT_ID:
            self.student_id_cell_triggered.emit(self._model.get_student_id_of_row(i_row))
        elif i_col == StudentTableColumns.COL_SCORE:
            self.mark_result_cell_triggered.emit(self._model.get_student_id_of_row(i_row))

    @pyqtSlot(StudentID)
    def _on_student_modification_observed(self, student_id: StudentID) -> None:
        """変更された学生一人を読み直し、元の行位置へ反映する。"""
        try:
            row = self._student_table_load_usecase.execute_row(student_id)
            self._model.replace_row(row)
        except Exception:
            self._logger.exception("学生行の再読み込みに失敗しました: %s", student_id)

    def shutdown(self) -> None:
        """ウィジェット終了時に学生変更の購読を解除する。"""
        self._student_change_bridge.stop()

    def mouseMoveEvent(self, evt: QMouseEvent):
        # 特定のセルに来たらマウスカーソルの形を変える
        index = self.indexAt(evt.pos())
        if not index.isValid():
            return
        if index.column() in (StudentTableColumns.COL_STUDENT_ID, StudentTableColumns.COL_SCORE):
            # noinspection PyTypeChecker
            self.viewport().setCursor(Qt.PointingHandCursor)
        else:
            self.viewport().unsetCursor()
