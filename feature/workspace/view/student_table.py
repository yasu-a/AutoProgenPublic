from functools import cache

from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex, pyqtSignal
from PyQt5.QtGui import QMouseEvent, QFont, QColor
from PyQt5.QtWidgets import QTableView

from feature.workspace.handler.interface import StudentTableRowViewModel, IStudentTableView, \
    IStudentTableHandler
from shared.domain.model.stage import Stage
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

    @classmethod
    def stage_to_column(cls, stage: Stage) -> int:
        assert stage in Stage, f"stage must be a Stage: {stage}"
        return {
            Stage.BUILD: cls.COL_STAGE_BUILD,
            Stage.COMPILE: cls.COL_STAGE_COMPILE,
            Stage.EXECUTE: cls.COL_STAGE_EXECUTE,
            Stage.TEST: cls.COL_STAGE_TEST,
        }[stage]


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
        current_id_map = {row.student_id: i for i,
                          row in enumerate(self._rows)}

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
        # 表示用テキスト (DisplayRole)
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
        # フォント設定 (FontRole) - リンクなど
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
        # 文字色設定 (ForegroundRole) - リンク色、OK/NG色
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
        # 背景色設定 (BackgroundRole) - 実行中のステージ
        # -------------------------------------------------------------------
        elif role == Qt.BackgroundRole:
            if row_data.processing_stage is not None:
                if col == StudentTableColumns.stage_to_column(row_data.processing_stage):
                    return QColor("orange").lighter()
            return None

        # -------------------------------------------------------------------
        # 配置設定 (TextAlignmentRole) - 中央揃え
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
        # ツールチップ (ToolTipRole) - エラー詳細
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
        min_width = max(self.columnWidth(col)
                        for col in StudentTableColumns.list_stage_columns())
        for col in StudentTableColumns.list_stage_columns():
            self.setColumnWidth(col, min_width)

    def on_student_id_clicked(self, student_id: StudentID):
        if len(self.selectedIndexes()) != 1:
            return

        i_row, i_col = self.currentIndex().row(), self.currentIndex().column()
        if i_col == StudentTableColumns.COL_STUDENT_ID:
            # noinspection PyUnresolvedReferences
            self.student_id_clicked.emit(student_id)
        elif i_col == StudentTableColumns.COL_SCORE:
            # noinspection PyUnresolvedReferences
            self.score_clicked.emit(student_id)

    def on_sore_clicked(self, student_id: StudentID):
        raise NotImplementedError()

    def get_parent_widget(self):
        """親ウィジェットを取得（QObjectのparent用）"""
        return self
