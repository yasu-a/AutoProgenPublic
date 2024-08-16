from datetime import datetime
from typing import Any, Callable, Iterable

from PyQt5.QtCore import *
from PyQt5.QtGui import QColor, QWheelEvent, QFont
from PyQt5.QtWidgets import *

from app_logging import create_logger
from domain.models.stages import StudentProgressStage, AbstractStudentProgress
from domain.models.values import StudentID
from fonts import font
from service_provider import get_project_service


class StudentTableColumns:
    COL_STUDENT_ID = 0
    COL_NAME = 1
    COL_STAGE_BUILD = 2
    COL_STAGE_COMPILE = 3
    COL_STAGE_EXECUTE = 4
    COL_ERROR = 5
    COL_TESTCASE_RESULT = 6
    COL_MARK_RESULT = 7
    HEADER = "学籍番号", "名前", "実行環境構築", "コンパイル", "実行", "エラー", "テスト結果", "採点結果"


QtRoleType = int


def data_provider(*, column: int):
    def decorator(f: Callable[[StudentID, QtRoleType], Any]):
        setattr(f, "_cell_provider_column", column)
        return f

    return decorator


class StudentTableModelDataProvider:
    def __init__(self, student_ids: list[StudentID]):
        self._student_ids = student_ids
        self._project_service = get_project_service()
        self._logger = create_logger(name=f"{type(self).__name__}")

    @classmethod
    def _font_link_text(cls) -> QFont:
        f = font(monospace=True)
        f.setBold(True)
        f.setUnderline(True)
        return f

    @classmethod
    def _foreground_link_text(cls) -> QColor:
        return QColor("blue")

    @data_provider(
        column=StudentTableColumns.COL_STUDENT_ID,
    )
    def get_display_role_of_student_id(self, student_id: StudentID, role: QtRoleType):
        if role == Qt.DisplayRole:
            return str(student_id)
        elif role == Qt.FontRole:
            return self._font_link_text()
        elif role == Qt.ForegroundRole:
            return self._foreground_link_text()

    @data_provider(
        column=StudentTableColumns.COL_NAME,
    )
    def get_display_role_of_name(self, student_id: StudentID, role: QtRoleType):
        if role == Qt.DisplayRole:
            return self._project_service.get_student_meta(student_id).name

    def _get_student_progress(self, student_id: StudentID) -> AbstractStudentProgress:
        return self._project_service.get_student_progress(student_id)

    def _get_display_role_of_student_stage(
            self,
            student_id: StudentID,
            stage: StudentProgressStage,
    ):
        if self._project_service.is_student_stage_finished(student_id, stage):
            result = self._project_service.get_student_stage_result(student_id, stage)
            if result.is_success():
                return "✔"
            else:
                return "エラー"

    @data_provider(
        column=StudentTableColumns.COL_STAGE_BUILD,
    )
    def get_display_role_of_stage_build(self, student_id: StudentID, role: QtRoleType):
        if role == Qt.DisplayRole:
            return self._get_display_role_of_student_stage(
                student_id=student_id,
                stage=StudentProgressStage.BUILD,
            )

    @data_provider(
        column=StudentTableColumns.COL_STAGE_COMPILE,
    )
    def get_display_role_of_stage_compile(self, student_id: StudentID, role: QtRoleType):
        if role == Qt.DisplayRole:
            return self._get_display_role_of_student_stage(
                student_id=student_id,
                stage=StudentProgressStage.COMPILE,
            )

    @data_provider(
        column=StudentTableColumns.COL_STAGE_EXECUTE,
    )
    def get_display_role_of_stage_execute(self, student_id: StudentID, role: QtRoleType):
        if role == Qt.DisplayRole:
            return self._get_display_role_of_student_stage(
                student_id=student_id,
                stage=StudentProgressStage.EXECUTE,
            )

    @data_provider(
        column=StudentTableColumns.COL_ERROR,
    )
    def get_display_role_of_error(self, student_id: StudentID, role: QtRoleType):
        if role == Qt.DisplayRole:
            return self._get_student_progress(
                student_id=student_id,
            ).get_main_reason()
        elif role == Qt.ToolTipRole:
            return self._get_student_progress(
                student_id=student_id,
            ).get_detailed_reason()

    @data_provider(
        column=StudentTableColumns.COL_TESTCASE_RESULT,
    )
    def get_display_role_of_testcase_result(self, student_id: StudentID, role: QtRoleType):
        return None

    @data_provider(
        column=StudentTableColumns.COL_MARK_RESULT,
    )
    def get_display_role_of_mark_result(self, student_id: StudentID, role: QtRoleType):
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

        project_service = get_project_service()
        self._student_ids: list[StudentID] = project_service.get_student_ids()

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

    def get_student_id_of_row(self, i_row: int):
        return self._student_ids[i_row]


class _StudentObserver(QObject):
    student_modified = pyqtSignal(StudentID)

    @staticmethod
    def __student_id_cyclic_iterator(student_ids: list[StudentID]) -> Iterable[StudentID]:
        while True:
            for student_id in student_ids:
                yield student_id

    def __init__(self, parent: QObject):
        super().__init__(parent)

        self._service = get_project_service()
        self._student_id_iter = iter(
            self.__student_id_cyclic_iterator(self._service.get_student_ids())
        )

        self._timer = QTimer(self)
        self._timer.setInterval(20)
        self._timer.timeout.connect(self._on_timer_timeout)  # type: ignore
        self._timer.start()

        self._student_id_mtime_mapping: dict[StudentID, datetime | None] = {}
        self._current_student_index = 0

    @pyqtSlot()
    def _on_timer_timeout(self):
        student_id = next(self._student_id_iter)
        prev_mtime = self._student_id_mtime_mapping.get(student_id)
        current_mtime = self._service.get_student_mtime(student_id)
        if prev_mtime != current_mtime:
            if prev_mtime is not None:  # 初めて巡回したときは更新を行わない
                # noinspection PyUnresolvedReferences
                self.student_modified.emit(student_id)
        self._student_id_mtime_mapping[student_id] = current_mtime


class StudentTableWidget(QTableView):
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
            get_project_service().show_student_submission_folder_in_explorer(
                self._model.get_student_id_of_row(i_row)
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

    # https://stackoverflow.com/questions/38234021/horizontal-scroll-on-wheelevent-with-shift-too-fast
    # noinspection DuplicatedCode
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
