from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSplitter, QListWidget, QTableWidget, QTableWidgetItem, QSpinBox, QFileDialog,
    QAbstractItemView, QHeaderView, QSizePolicy,
)

from feature.export.domain.value import ExcelColumnMapping, ExcelRowRange
from shared.view.style.font import get_font


# プレビューテーブルの色定義
class ExcelPreviewColors:
    """Excelプレビューテーブルの色定義"""
    # テーブル背景色
    STUDENT_ID = QColor("#E3F2FD")  # 薄い青
    STUDENT_NAME = QColor("#E8F5E9")  # 薄い緑
    SCORE_WRITE = QColor("#FFF3E0")  # 薄いオレンジ
    QUESTION_HEADER = QColor("#F3E5F5")  # 薄い紫

    # ラベル用の色（テーブル背景色に対応）
    STUDENT_ID_LABEL = QColor("#2196F3")  # 青（学籍番号列ラベル用）
    STUDENT_NAME_LABEL = QColor("#4CAF50")  # 緑（氏名列ラベル用）
    SCORE_WRITE_LABEL = QColor("#FF9800")  # オレンジ（書き込み列ラベル用）

    # メッセージ欄用の色
    MESSAGE_SUCCESS_BG = QColor("#E8F5E9")  # 成功メッセージ背景色（薄い緑）
    MESSAGE_SUCCESS_FG = QColor("#2E7D32")  # 成功メッセージ文字色（濃い緑）
    MESSAGE_ERROR_BG = QColor("#FFEBEE")  # エラーメッセージ背景色（薄い赤）
    MESSAGE_ERROR_FG = QColor("#C62828")  # エラーメッセージ文字色（濃い赤）


class ExcelScoreExportTab(QWidget):
    """Excel書き出し用のタブ"""

    # シート選択が変更されたときのシグナル
    sheet_selection_changed = pyqtSignal()
    # ファイル選択が変更されたときのシグナル
    file_path_changed = pyqtSignal(str)
    # マッピング設定が変更されたときのシグナル
    mapping_changed = pyqtSignal()

    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self._current_sheet_data: dict[tuple[int, int], str] | None = None
        self._current_mapping: ExcelColumnMapping | None = None
        self._current_row_range: ExcelRowRange | None = None
        self._current_target_id_col: int | None = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)  # 余白を最小化
        layout.setSpacing(5)  # 要素間のスペースを最小化
        self.setLayout(layout)

        # ファイル選択
        layout_file = QHBoxLayout()
        layout.addLayout(layout_file)
        layout_file.addWidget(QLabel("Excelファイル:", self))
        self._le_excel_path = QLineEdit(self)
        self._le_excel_path.setReadOnly(True)
        layout_file.addWidget(self._le_excel_path)
        self._b_select_file = QPushButton("選択", self)
        layout_file.addWidget(self._b_select_file)

        # メインエリア（Splitter）
        splitter = QSplitter(self)
        # Splitterを縦方向に拡張可能にする
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(splitter)

        # 左：シート一覧
        self._list_sheets = QListWidget(self)
        self._list_sheets.setMaximumWidth(200)
        splitter.addWidget(self._list_sheets)

        # 右：シートプレビュー
        self._table_preview = QTableWidget(self)
        self._table_preview.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # フォントサイズを小さく設定
        self._table_preview.setFont(get_font(small=True))
        # 列見出しの境界をダブルクリックでリサイズできるようにする
        self._table_preview.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        # 行の高さを小さく設定
        self._table_preview.verticalHeader().setDefaultSectionSize(20)
        splitter.addWidget(self._table_preview)

        splitter.setSizes([200, 600])

        # 設定エリア
        layout_settings = QVBoxLayout()
        layout_settings.setContentsMargins(0, 0, 0, 0)  # 余白を最小化
        layout_settings.setSpacing(3)  # 要素間のスペースを最小化
        layout.addLayout(layout_settings)

        # 1行目：列番号設定（学籍番号列、氏名列、書き込み列を横並び）
        layout_row1 = QHBoxLayout()
        layout_row1.setSpacing(5)  # ラベルとスピンボックスの間の隙間を最小化
        layout_settings.addLayout(layout_row1)

        # 等間隔配置のため、先頭にStretchを追加
        layout_row1.addStretch()

        # 学籍番号列
        self._lbl_student_id = QLabel(self)
        self._lbl_student_id.setTextFormat(Qt.RichText)
        student_id_color = ExcelPreviewColors.STUDENT_ID_LABEL.name()
        self._lbl_student_id.setText(
            f'<span style="color: {student_id_color}; font-size: 14px;">●</span> 学籍番号列:')
        layout_row1.addWidget(self._lbl_student_id)
        self._sb_student_id_col = QSpinBox(self)
        self._sb_student_id_col.setRange(0, 1000)  # 0=未設定、1-1000=1-based表示
        self._sb_student_id_col.setSpecialValueText("列 未設定")
        self._sb_student_id_col.setValue(0)  # 初期値は未設定
        # noinspection PyUnresolvedReferences
        self._sb_student_id_col.valueChanged.connect(
            self.__on_mapping_value_changed)
        layout_row1.addWidget(self._sb_student_id_col)

        # 等間隔配置のため、セット間にStretchを追加
        layout_row1.addStretch()

        # 氏名列
        self._lbl_student_name = QLabel(self)
        self._lbl_student_name.setTextFormat(Qt.RichText)
        student_name_color = ExcelPreviewColors.STUDENT_NAME_LABEL.name()
        self._lbl_student_name.setText(
            f'<span style="color: {student_name_color}; font-size: 14px;">●</span> 氏名列:')
        layout_row1.addWidget(self._lbl_student_name)
        self._sb_student_name_col = QSpinBox(self)
        self._sb_student_name_col.setRange(0, 1000)  # 0=未設定、1-1000=1-based表示
        self._sb_student_name_col.setSpecialValueText("列 未設定")
        self._sb_student_name_col.setValue(0)  # 初期値は未設定
        # noinspection PyUnresolvedReferences
        self._sb_student_name_col.valueChanged.connect(
            self.__on_mapping_value_changed)
        layout_row1.addWidget(self._sb_student_name_col)

        # 等間隔配置のため、セット間にStretchを追加
        layout_row1.addStretch()

        # 書き込み列
        self._lbl_score = QLabel(self)
        self._lbl_score.setTextFormat(Qt.RichText)
        score_write_color = ExcelPreviewColors.SCORE_WRITE_LABEL.name()
        self._lbl_score.setText(
            f'<span style="color: {score_write_color}; font-size: 14px;">●</span> 書き込み列:')
        layout_row1.addWidget(self._lbl_score)
        self._sb_score_col = QSpinBox(self)
        self._sb_score_col.setRange(0, 1000)  # 0=未設定、1-1000=1-based表示
        self._sb_score_col.setSpecialValueText("列 未設定")
        self._sb_score_col.setValue(0)  # 初期値は未設定
        # noinspection PyUnresolvedReferences
        self._sb_score_col.valueChanged.connect(
            self.__on_mapping_value_changed)
        layout_row1.addWidget(self._sb_score_col)

        # 等間隔配置のため、末尾にStretchを追加
        layout_row1.addStretch()

        # 2行目：行番号（開始 ～ 終了）
        layout_row2 = QHBoxLayout()
        layout_row2.setSpacing(5)  # ラベルとスピンボックスの間の隙間を最小化
        layout_settings.addLayout(layout_row2)

        # 水平中央配置のため、先頭にStretchを追加
        layout_row2.addStretch()

        layout_row2.addWidget(QLabel("行番号:", self))
        self._sb_start_row = QSpinBox(self)
        self._sb_start_row.setRange(0, 9999)  # 0=未設定、1-9999=1-based表示
        self._sb_start_row.setSpecialValueText("開始行 未設定")
        self._sb_start_row.setValue(0)  # 初期値は未設定
        # noinspection PyUnresolvedReferences
        self._sb_start_row.valueChanged.connect(
            self.__on_mapping_value_changed)
        layout_row2.addWidget(self._sb_start_row)
        layout_row2.addWidget(QLabel("～", self))
        self._sb_end_row = QSpinBox(self)
        self._sb_end_row.setRange(0, 9999)  # 0=未設定、1-9999=1-based表示
        self._sb_end_row.setSpecialValueText("終了行 未設定")
        self._sb_end_row.setValue(0)  # 初期値は未設定
        # noinspection PyUnresolvedReferences
        self._sb_end_row.valueChanged.connect(self.__on_mapping_value_changed)
        layout_row2.addWidget(self._sb_end_row)

        # 水平中央配置のため、末尾にStretchを追加
        layout_row2.addStretch()

        # メッセージ欄
        layout_message = QHBoxLayout()
        layout_message.setContentsMargins(0, 0, 0, 0)  # 余白を最小化
        layout.addLayout(layout_message)
        self._lbl_message = QLabel(self)
        self._lbl_message.setWordWrap(True)
        self._lbl_message.setText("")  # 初期状態は空
        self._lbl_message.setStyleSheet("padding: 4px;")  # パディングを減らす
        layout_message.addWidget(self._lbl_message)

        # シグナル接続
        # noinspection PyUnresolvedReferences
        self._b_select_file.clicked.connect(self.__b_select_file_clicked)
        # noinspection PyUnresolvedReferences
        self._list_sheets.currentItemChanged.connect(
            self.__list_sheets_selection_changed)

    @pyqtSlot()
    def __b_select_file_clicked(self):
        """ファイル選択ボタンがクリックされたとき"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Excelファイルを選択", "", "Excelファイル (*.xlsx)"
        )
        if file_path:
            self._le_excel_path.setText(file_path)
            # noinspection PyUnresolvedReferences
            self.file_path_changed.emit(file_path)

    @pyqtSlot()
    def __list_sheets_selection_changed(self):
        """シート選択が変更されたとき"""
        # noinspection PyUnresolvedReferences
        self.sheet_selection_changed.emit()

    @pyqtSlot()
    def __on_mapping_value_changed(self):
        """スピンボックスの値が変更されたとき、シグナルを発行"""
        # noinspection PyUnresolvedReferences
        self.mapping_changed.emit()

    def set_excel_path(self, path: str) -> None:
        """Excelファイルパスを設定"""
        self._le_excel_path.setText(path)

    def get_excel_path(self) -> str:
        """Excelファイルパスを取得"""
        return self._le_excel_path.text()

    def set_sheet_names(self, names: list[str]) -> None:
        """シート名リストを設定"""
        self._list_sheets.clear()
        for name in names:
            self._list_sheets.addItem(name)

    def get_selected_sheet_name(self) -> str | None:
        """選択中のシート名を取得"""
        current_item = self._list_sheets.currentItem()
        if current_item is None:
            return None
        return current_item.text()

    def set_sheet_preview_data(
            self,
            data: dict[tuple[int, int], str],
            target_id_col: int | None = None,
    ) -> None:
        """シートプレビューデータを設定"""
        self._current_sheet_data = data
        self._current_target_id_col = target_id_col

        if not data:
            self._table_preview.setRowCount(0)
            self._table_preview.setColumnCount(0)
            return

        # 最大の行インデックスと列インデックスを取得
        max_row = max(row for row, _ in data.keys())
        max_col = max(col for _, col in data.keys())

        # テーブルを設定
        self._table_preview.setRowCount(max_row + 1)
        self._table_preview.setColumnCount(max_col + 1)

        # データを設定（空セルも含める）
        for row in range(max_row + 1):
            for col in range(max_col + 1):
                value = data.get((row, col), "")
                item = QTableWidgetItem(value)
                self._table_preview.setItem(row, col, item)

        # 各列をコンテンツにフィットさせる
        self._table_preview.resizeColumnsToContents()

        # 色を更新（初期設定時はマッピングが設定されていないのでスキップ）
        if self._current_mapping is not None and self._current_row_range is not None:
            self._update_preview_colors_internal()

    def update_preview_colors(self):
        """プレビューテーブルの色を更新（Handlerから呼ばれる）"""
        # 現在のスピンボックスの値からマッピング設定を取得
        if self._current_sheet_data is None:
            return

        # 未設定（0）の場合は色をつけない
        student_id_val = self._sb_student_id_col.value()
        student_name_val = self._sb_student_name_col.value()
        score_write_val = self._sb_score_col.value()
        start_row_val = self._sb_start_row.value()
        end_row_val = self._sb_end_row.value()

        if (student_id_val == 0
                or student_name_val == 0
                or score_write_val == 0
                or start_row_val == 0
                or end_row_val == 0):
            # 未設定の場合は色をつけない（すべて白にリセット）
            for row in range(self._table_preview.rowCount()):
                for col in range(self._table_preview.columnCount()):
                    item = self._table_preview.item(row, col)
                    if item:
                        item.setBackground(QColor("white"))
            return

        # スピンボックスの値（1-based）から0-basedに変換して設定を構築
        current_mapping = ExcelColumnMapping(
            student_id_column_index=student_id_val - 1,  # 1-basedから0-basedに変換
            student_name_column_index=student_name_val - 1,  # 1-basedから0-basedに変換
            score_write_column_index=score_write_val - 1,  # 1-basedから0-basedに変換
        )
        current_row_range = ExcelRowRange(
            start_row_index=start_row_val - 1,  # 1-basedから0-basedに変換
            end_row_index=end_row_val - 1,  # 1-basedから0-basedに変換
        )

        # 内部状態を更新
        self._current_mapping = current_mapping
        self._current_row_range = current_row_range

        # 色を更新
        self._update_preview_colors_internal()

    def _update_preview_colors_internal(self):
        """プレビューテーブルの色を更新（内部実装）"""
        if self._current_sheet_data is None or self._current_mapping is None or self._current_row_range is None:
            return

        # すべてのセルの背景色をリセット
        for row in range(self._table_preview.rowCount()):
            for col in range(self._table_preview.columnCount()):
                item = self._table_preview.item(row, col)
                if item:
                    item.setBackground(QColor("white"))

        start_row = self._current_row_range.start_row_index
        end_row = self._current_row_range.end_row_index
        id_col = self._current_mapping.student_id_column_index
        name_col = self._current_mapping.student_name_column_index
        score_col = self._current_mapping.score_write_column_index

        # 学籍番号範囲の色付け
        for r in range(start_row, end_row + 1):
            item = self._table_preview.item(r, id_col)
            if item:
                item.setBackground(ExcelPreviewColors.STUDENT_ID)

        # 氏名範囲の色付け
        for r in range(start_row, end_row + 1):
            item = self._table_preview.item(r, name_col)
            if item:
                item.setBackground(ExcelPreviewColors.STUDENT_NAME)

        # 書き込み範囲の色付け
        for r in range(start_row, end_row + 1):
            item = self._table_preview.item(r, score_col)
            if item:
                item.setBackground(ExcelPreviewColors.SCORE_WRITE)

        # 問Xセルの色付け（ヘッダー行を探す）
        if self._current_target_id_col is not None:
            # ヘッダー行は通常start_row - 1
            header_row = start_row - 1
            if header_row >= 0:
                item = self._table_preview.item(
                    header_row, self._current_target_id_col)
                if item:
                    item.setBackground(ExcelPreviewColors.QUESTION_HEADER)

    def show_message(self, message: str, is_success: bool = True) -> None:
        """メッセージを表示"""
        self._lbl_message.setText(message)
        if is_success:
            bg_color = ExcelPreviewColors.MESSAGE_SUCCESS_BG.name()
            fg_color = ExcelPreviewColors.MESSAGE_SUCCESS_FG.name()
            self._lbl_message.setStyleSheet(
                f"padding: 4px; background-color: {bg_color}; color: {fg_color};")
        else:
            bg_color = ExcelPreviewColors.MESSAGE_ERROR_BG.name()
            fg_color = ExcelPreviewColors.MESSAGE_ERROR_FG.name()
            self._lbl_message.setStyleSheet(
                f"padding: 4px; background-color: {bg_color}; color: {fg_color};")

    def clear_message(self) -> None:
        """メッセージをクリア"""
        self._lbl_message.setText("")
        self._lbl_message.setStyleSheet("padding: 4px;")

    def get_mapping_settings(self) -> tuple[ExcelColumnMapping, ExcelRowRange]:
        """マッピング設定を取得"""
        student_id_val = self._sb_student_id_col.value()
        student_name_val = self._sb_student_name_col.value()
        score_write_val = self._sb_score_col.value()
        start_row_val = self._sb_start_row.value()
        end_row_val = self._sb_end_row.value()

        # 未設定（0）の場合はエラー
        if (student_id_val == 0 or student_name_val == 0 or score_write_val == 0 or
                start_row_val == 0 or end_row_val == 0):
            raise ValueError("マッピング設定が未設定です。")

        mapping = ExcelColumnMapping(
            student_id_column_index=student_id_val - 1,  # 1-basedから0-basedに変換
            student_name_column_index=student_name_val - 1,  # 1-basedから0-basedに変換
            score_write_column_index=score_write_val - 1,  # 1-basedから0-basedに変換
        )

        row_range = ExcelRowRange(
            start_row_index=start_row_val - 1,  # 1-basedから0-basedに変換
            end_row_index=end_row_val - 1,  # 1-basedから0-basedに変換
        )

        return mapping, row_range

    def set_mapping_settings(
            self,
            mapping: ExcelColumnMapping | None = None,
            row_range: ExcelRowRange | None = None,
            target_id_col: int | None = None,
    ) -> None:
        """マッピング設定を設定（Noneの場合は未設定にする）"""
        if mapping is None or row_range is None:
            # 未設定にする
            self._sb_student_id_col.setValue(0)
            self._sb_student_name_col.setValue(0)
            self._sb_score_col.setValue(0)
            self._sb_start_row.setValue(0)
            self._sb_end_row.setValue(0)
            self._current_mapping = None
            self._current_row_range = None
            self._current_target_id_col = None
            # 色をリセット
            if self._current_sheet_data is not None:
                for row in range(self._table_preview.rowCount()):
                    for col in range(self._table_preview.columnCount()):
                        item = self._table_preview.item(row, col)
                        if item:
                            item.setBackground(QColor("white"))
            return

        self._current_mapping = mapping
        self._current_row_range = row_range
        self._current_target_id_col = target_id_col

        # マッピング設定を1-basedに変換して設定
        self._sb_student_id_col.setValue(mapping.student_id_column_index + 1)
        self._sb_student_name_col.setValue(mapping.student_name_column_index + 1)
        self._sb_score_col.setValue(mapping.score_write_column_index + 1)
        self._sb_start_row.setValue(row_range.start_row_index + 1)
        self._sb_end_row.setValue(row_range.end_row_index + 1)

        # 色を更新
        if self._current_sheet_data is not None:
            self._update_preview_colors_internal()
