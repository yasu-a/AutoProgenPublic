from functools import cache

from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex, pyqtSignal
from PyQt5.QtGui import QMouseEvent, QFont, QColor
from PyQt5.QtWidgets import QTableView

from feature.workspace.handler.interface import StudentTableRowViewModel, IStudentTableView, \
    IStudentTableHandler
from shared.domain.value.identifier import StudentID
from shared.view.mixin_shift_horizontal_scroll import HorizontalScrollWithShiftAndWheelMixin
from shared.view.style.font import get_font


class StudentTableColumns:
    """カラムのインデックス定義"""
    COL_STUDENT_ID = 0
    COL_NAME = 1
    COL_STAGE_BUILD = 2
    COL_STAGE_COMPILE = 3
    COL_STAGE_EXECUTE = 4
    COL_STAGE_TEST = 5
    COL_SCORE = 6
    COL_ERROR = 7

    @classmethod
    def list_stage_columns(cls):
        return (
            cls.COL_STAGE_BUILD,
            cls.COL_STAGE_COMPILE,
            cls.COL_STAGE_EXECUTE,
            cls.COL_STAGE_TEST,
        )


class SimpleStudentTableModel(QAbstractTableModel):
    """
    データ取得ロジックを持たない、純粋なデータ保持用モデル
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: list[StudentTableRowViewModel] = []

        # ヘッダー定義
        self._headers = [
            "学籍番号",
            "氏名",
            "Build",
            "Compile",
            "Execute",
            "Test",
            "点数",
            "エラー概要"
        ]

    def update_rows(self, new_rows: list[StudentTableRowViewModel]):
        """
        データを更新する（Upsert処理）
        - 既存のIDがあれば値を更新し、変更通知を出す
        - 新規のIDなら行を追加する
        """
        # 1. 現在のデータ位置を高速検索するためのマップを作成
        #    { StudentID: row_index }
        current_id_map = {row.student_id: i for i, row in enumerate(self._rows)}

        rows_to_insert = []

        for new_row in new_rows:
            idx = current_id_map.get(new_row.student_id)

            if idx is not None:
                # === ケースA: 既存行の更新 ===
                current_row = self._rows[idx]

                # データクラス同士を比較し、変更がある場合のみ処理する
                # (@dataclass(frozen=True) なら == で全フィールド比較が可能)
                if current_row != new_row:
                    self._rows[idx] = new_row

                    # Qtに変更を通知 (左端のカラムから右端のカラムまで)
                    top_left = self.index(idx, 0)
                    bottom_right = self.index(idx, self.columnCount() - 1)
                    self.dataChanged.emit(top_left, bottom_right)
            else:
                # === ケースB: 新規行 ===
                # 後でまとめて追加するためにリストに入れておく
                rows_to_insert.append(new_row)

        # === ケースBの続き: 行の追加処理 ===
        if rows_to_insert:
            start_idx = len(self._rows)
            end_idx = start_idx + len(rows_to_insert) - 1

            # 挿入開始を通知
            self.beginInsertRows(QModelIndex(), start_idx, end_idx)

            # データを追加
            self._rows.extend(rows_to_insert)

            # 挿入完了を通知
            self.endInsertRows()

    def get_row_data(self, index: QModelIndex) -> StudentTableRowViewModel | None:
        """指定されたインデックスのViewModelを取得（クリックイベント用など）"""
        if not index.isValid():
            return None
        row = index.row()
        if 0 <= row < len(self._rows):
            return self._rows[row]
        return None

    def get_student_id_of_row(self, row_idx: int) -> StudentID:
        """指定された行のStudentIDを取得（Viewからの呼び出し用）"""
        if 0 <= row_idx < len(self._rows):
            return self._rows[row_idx].student_id
        raise ValueError(f"Invalid row index: {row_idx}")

    # ===== QAbstractTableModel 実装 =====
    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._headers)

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

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None

        row_idx = index.row()
        if row_idx >= len(self._rows):
            return None

        row_data: StudentTableRowViewModel = self._rows[row_idx]
        col = index.column()

        # -------------------------------------------------------------------
        # 1. 表示用テキスト (DisplayRole)
        # -------------------------------------------------------------------
        if role == Qt.DisplayRole:
            if col == StudentTableColumns.COL_STUDENT_ID:
                return str(row_data.student_id)
            elif col == StudentTableColumns.COL_NAME:
                return row_data.name
            elif col == StudentTableColumns.COL_STAGE_BUILD:
                return row_data.build_stage_status
            elif col == StudentTableColumns.COL_STAGE_COMPILE:
                return row_data.compile_stage_status
            elif col == StudentTableColumns.COL_STAGE_EXECUTE:
                return " ".join(row_data.execute_stage_status_lst)
            elif col == StudentTableColumns.COL_STAGE_TEST:
                return " ".join(row_data.test_stage_status_lst)
            elif col == StudentTableColumns.COL_SCORE:
                return row_data.score
            elif col == StudentTableColumns.COL_ERROR:
                return row_data.error_summary

        # -------------------------------------------------------------------
        # 2. フォント設定 (FontRole) - リンクなど
        # -------------------------------------------------------------------
        elif role == Qt.FontRole:
            if col == StudentTableColumns.COL_STUDENT_ID:
                if row_data.has_submission:
                    return self._font_link_text(monospace=True)
                else:
                    return self._font_dead_link_text(monospace=True)
            elif col == StudentTableColumns.COL_SCORE:
                return self._font_link_text(monospace=False)

        # -------------------------------------------------------------------
        # 3. 文字色設定 (ForegroundRole) - リンク色、OK/NG色
        # -------------------------------------------------------------------
        elif role == Qt.ForegroundRole:
            if col == StudentTableColumns.COL_STUDENT_ID:
                if row_data.has_submission:
                    return self._foreground_link_text()
                else:
                    return self._foreground_dead_link_text()

            elif col == StudentTableColumns.COL_SCORE:
                return self._foreground_link_text()

            elif col == StudentTableColumns.COL_ERROR:
                if row_data.error_summary:
                    return QColor("red")

            # ステージ列の色分け (OK=緑, NG=赤)
            # ※ Handler側で設定された記号(✔/⚠)が含まれているかで判定
            elif col in (StudentTableColumns.COL_STAGE_BUILD,
                         StudentTableColumns.COL_STAGE_COMPILE,
                         StudentTableColumns.COL_STAGE_EXECUTE,
                         StudentTableColumns.COL_STAGE_TEST):
                text = self.data(index, Qt.DisplayRole)
                if "⚠" in text:
                    return QColor("red")
                elif "✔" in text:
                    return QColor("limegreen")

        # -------------------------------------------------------------------
        # 4. 配置設定 (TextAlignmentRole) - 中央揃え
        # -------------------------------------------------------------------
        elif role == Qt.TextAlignmentRole:
            # IDと点数は中央揃え
            if col == StudentTableColumns.COL_STUDENT_ID or col == StudentTableColumns.COL_SCORE:
                return Qt.AlignCenter
            # ステージ状態も中央揃え
            if col in [StudentTableColumns.COL_STAGE_BUILD, StudentTableColumns.COL_STAGE_COMPILE,
                       StudentTableColumns.COL_STAGE_EXECUTE, StudentTableColumns.COL_STAGE_TEST]:
                return Qt.AlignCenter

        # -------------------------------------------------------------------
        # 5. ツールチップ (ToolTipRole) - エラー詳細
        # -------------------------------------------------------------------
        elif role == Qt.ToolTipRole:
            if col == StudentTableColumns.COL_ERROR and row_data.error_summary:
                return row_data.error_summary

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section < len(self._headers):
                return self._headers[section]
        return None


class StudentTableView(QTableView, HorizontalScrollWithShiftAndWheelMixin, IStudentTableView):
    student_id_clicked = pyqtSignal(StudentID)
    score_clicked = pyqtSignal(StudentID)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._handler: IStudentTableHandler

        self._model = SimpleStudentTableModel(self)
        self.setModel(self._model)

        self._init_ui()

    def set_handler(self, handler: IStudentTableHandler):
        # noinspection PyAttributeOutsideInit
        self._handler = handler
        # noinspection PyUnresolvedReferences
        self.student_id_clicked.connect(self._handler.on_student_id_clicked)
        # noinspection PyUnresolvedReferences
        self.score_clicked.connect(self._handler.on_sore_clicked)

    def _init_ui(self):
        # 見た目の調整
        self.setSelectionBehavior(QTableView.SelectRows)  # 行単位で選択
        self.setSelectionMode(QTableView.SingleSelection)  # 複数選択不可
        self.verticalHeader().setVisible(False)  # 行番号（1, 2, 3...）を隠す

        # カラム幅の調整（最後の列を伸ばすなど）
        header = self.horizontalHeader()
        header.setStretchLastSection(True)

        # マウス追跡を有効化（カーソル変更用）
        self.setMouseTracking(True)

        # カラム幅の固定設定 (旧実装の再現)
        self.setColumnWidth(StudentTableColumns.COL_STUDENT_ID, 200)
        self.setColumnWidth(StudentTableColumns.COL_NAME, 200)
        self.setColumnWidth(StudentTableColumns.COL_STAGE_BUILD, 150)
        self.setColumnWidth(StudentTableColumns.COL_STAGE_COMPILE, 150)
        self.setColumnWidth(StudentTableColumns.COL_STAGE_EXECUTE, 150)
        self.setColumnWidth(StudentTableColumns.COL_STAGE_TEST, 150)
        self.setColumnWidth(StudentTableColumns.COL_SCORE, 100)
        self.setColumnWidth(StudentTableColumns.COL_ERROR, 400)

        # 行の高さ
        self.verticalHeader().setDefaultSectionSize(20)

        self.clicked.connect(self._on_cell_clicked)

    def _on_cell_clicked(self, index: QModelIndex):
        if not index.isValid():
            return

        row_data = self._model.get_row_data(index)
        if not row_data:
            return

        col = index.column()
        # ID列のクリック
        if col == StudentTableColumns.COL_STUDENT_ID:
            # 提出フォルダがない(リンク切れ)場合は発火しない制御もここに入れられます
            if row_data.has_submission:
                # noinspection PyUnresolvedReferences
                self.student_id_clicked.emit(row_data.student_id)

        # 点数列のクリック
        elif col == StudentTableColumns.COL_SCORE:
            # noinspection PyUnresolvedReferences
            self.score_clicked.emit(row_data.student_id)

    def mouseMoveEvent(self, evt: QMouseEvent):
        """マウスカーソルの制御"""
        index = self.indexAt(evt.pos())
        if not index.isValid():
            self.viewport().unsetCursor()
            super().mouseMoveEvent(evt)
            return

        col: int = index.column()
        row_data: StudentTableRowViewModel = self._model.get_row_data(index)

        # リンク可能な列でカーソルを変える
        is_link = False
        if col == StudentTableColumns.COL_STUDENT_ID:
            if row_data.has_submission:
                is_link = True
        elif col == StudentTableColumns.COL_SCORE:
            is_link = True

        # ID列の場合は提出があるときだけリンクカーソルにする等の制御も可能
        if is_link:
            self.viewport().setCursor(Qt.PointingHandCursor)
        else:
            self.viewport().unsetCursor()

        super().mouseMoveEvent(evt)

    def update_table_data(self, view_models: list[StudentTableRowViewModel]):
        """Handlerから呼ばれる：データを更新する"""
        self._model.update_rows(view_models)
        self.resizeColumnsToContents()

        # ステージ列の幅を最大のコンテンツ幅で統一
        min_width = max(self.columnWidth(col) for col in StudentTableColumns.list_stage_columns())
        for col in StudentTableColumns.list_stage_columns():
            self.setColumnWidth(col, min_width)

    def on_student_id_clicked(self, student_id: StudentID):

        if len(self.selectedIndexes()) != 1:
            return

        i_row, i_col = self.currentIndex().row(), self.currentIndex().column()
        if i_col == StudentTableColumns.COL_STUDENT_ID:
            self.student_id_cell_triggered.emit(self._model.get_student_id_of_row(i_row))
        elif i_col == StudentTableColumns.COL_SCORE:
            self.mark_result_cell_triggered.emit(self._model.get_student_id_of_row(i_row))

    def on_sore_clicked(self, student_id: StudentID):
        raise NotImplementedError()

    def get_parent_widget(self):
        """親ウィジェットを取得（QObjectのparent用）"""
        return self


"""
# 旧実装：

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
            cell_data = get_student_table_get_student_id_cell_data_usecase().execute(student_id)
            return cell_data.student_number
        elif role == Qt.FontRole:
            cell_data = get_student_table_get_student_id_cell_data_usecase().execute(student_id)
            if cell_data.is_submission_folder_link_alive:
                return self._font_link_text(monospace=True)
            else:
                return self._font_dead_link_text(monospace=True)
        elif role == Qt.ForegroundRole:
            cell_data = get_student_table_get_student_id_cell_data_usecase().execute(student_id)
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
            cell_data = get_student_table_get_student_name_cell_data_usecase().execute(student_id)
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
            cell_data = get_student_table_get_student_stage_state_cell_data_usecase().execute(
                student_id=student_id,
                stage_type=BuildStage,
            )
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
            cell_data = get_student_table_get_student_stage_state_cell_data_usecase().execute(
                student_id=student_id,
                stage_type=CompileStage,
            )
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
            cell_data = get_student_table_get_student_stage_state_cell_data_usecase().execute(
                student_id=student_id,
                stage_type=ExecuteStage,
            )
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
            cell_data = get_student_table_get_student_stage_state_cell_data_usecase().execute(
                student_id=student_id,
                stage_type=TestStage,
            )
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
        else:
            return None

    @data_provider(
        column=StudentTableColumns.COL_SCORE,
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
            provider: AbstractStudentTableModelDataProvider,
    ):
        super().__init__(parent)

        self._student_ids: list[StudentID] = provider.student_ids
        self._data_provider = provider

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
        else:
            return None

    def get_student_id_of_row(self, i_row: int) -> StudentID:
        return self._student_ids[i_row]


class _StudentObserver(QObject):
    _logger = create_logger()

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

        self._student_id_mtime_mapping: dict[StudentID, StudentStageResultDiffSnapshotDto] = {}
        self._current_student_index = 0

    @pyqtSlot()
    def _on_timer_timeout(self):
        # FIXME: 更新プロセスが動かないのでコメントアウト & poll方式じゃない実装にしたい
        pass
        # # 学籍番号の取得
        # student_id = next(self._student_id_iter)

        # # スナップショットを取得
        # new_snapshot = get_student_dynamic_take_diff_snapshot_usecase().execute(student_id)

        # # 初めて巡回したとき以外は更新を確認してシグナルを送出
        # if student_id in self._student_id_mtime_mapping:
        #     old_snapshot = self._student_id_mtime_mapping.get(student_id)
        #     if new_snapshot.is_modified_from(old_snapshot):
        #         # noinspection PyUnresolvedReferences
        #         self._logger.debug(
        #             f"StudentEntity {student_id} has been modified\n{old_snapshot}\n{new_snapshot}")
        #         self.student_modified.emit(student_id)

        # self._student_id_mtime_mapping[student_id] = new_snapshot


class StudentTableWidget(QTableView, HorizontalScrollWithShiftAndWheelMixin):
    _logger = create_logger()

    student_id_cell_triggered = pyqtSignal(StudentID, name="student_id_cell_triggered")
    mark_result_cell_triggered = pyqtSignal(StudentID, name="mark_result_cell_triggered")

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
        # noinspection PyTypeChecker
        self._model = StudentTableModel(
            self,
            provider=self._model_data_provider,
        )  # type: ignore
        self.setModel(self._model)

        self._init_ui()

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

        # シグナル接続
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
    def _on_student_modification_observed(self, student_id):
        i_row = self._model.get_row_of_student(student_id)
        self._logger.debug(f"Updating row {i_row} {student_id}")
        self._model_data_provider.invalidate_cache(i_row)
        index_begin = self._model.createIndex(i_row, 0)
        index_end = self._model.createIndex(i_row, self._model.columnCount() - 1)
        self.dataChanged(index_begin, index_end)

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
"""
