import json

from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QStackedWidget, QTableWidget, QTableWidgetItem, QPlainTextEdit,
    QFileDialog, QAbstractItemView,
)

from feature.export.domain.value import ScoreExportFormat
from feature.export.usecase.interface import SimpleScoreExportRowDto


class SimpleScoreExportTab(QWidget):
    """単純書き出し（CSV/JSON）用のタブ"""

    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # 出力先フォルダ
        layout_folder = QHBoxLayout()
        layout.addLayout(layout_folder)
        layout_folder.addWidget(QLabel("出力先フォルダ:", self))
        self._le_folder_path = QLineEdit(self)
        self._le_folder_path.setReadOnly(True)
        layout_folder.addWidget(self._le_folder_path)
        self._b_select_folder = QPushButton("選択", self)
        layout_folder.addWidget(self._b_select_folder)

        # ファイル名
        layout_filename = QHBoxLayout()
        layout.addLayout(layout_filename)
        layout_filename.addWidget(QLabel("ファイル名:", self))
        self._le_filename = QLineEdit(self)
        layout_filename.addWidget(self._le_filename)
        self._l_extension = QLabel(".csv", self)
        layout_filename.addWidget(self._l_extension)

        # 形式
        layout_format = QHBoxLayout()
        layout.addLayout(layout_format)
        layout_format.addWidget(QLabel("形式:", self))
        self._cb_format = QComboBox(self)
        self._cb_format.addItem("CSV", ScoreExportFormat.CSV)
        self._cb_format.addItem("JSON", ScoreExportFormat.JSON)
        layout_format.addWidget(self._cb_format)
        layout_format.addStretch()

        # プレビューエリア
        self._stacked_preview = QStackedWidget(self)
        layout.addWidget(self._stacked_preview)

        # CSVプレビュー（QTableWidget）
        self._table_preview = QTableWidget(self)
        self._table_preview.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table_preview.setColumnCount(3)
        self._table_preview.setHorizontalHeaderLabels(["学籍番号", "氏名", "点数"])
        self._stacked_preview.addWidget(self._table_preview)

        # JSONプレビュー（QPlainTextEdit）
        self._text_preview = QPlainTextEdit(self)
        self._text_preview.setReadOnly(True)
        self._stacked_preview.addWidget(self._text_preview)

        # シグナル接続
        # noinspection PyUnresolvedReferences
        self._b_select_folder.clicked.connect(self.__b_select_folder_clicked)
        # noinspection PyUnresolvedReferences
        self._cb_format.currentIndexChanged.connect(self.__cb_format_changed)

    @pyqtSlot()
    def __b_select_folder_clicked(self):
        """フォルダ選択ボタンがクリックされたとき"""
        folder = QFileDialog.getExistingDirectory(self, "出力先フォルダを選択")
        if folder:
            self._le_folder_path.setText(folder)

    @pyqtSlot(int)
    def __cb_format_changed(self, index: int):
        """形式が変更されたとき"""
        format_enum = self._cb_format.itemData(index)
        if format_enum == ScoreExportFormat.CSV:
            self._l_extension.setText(".csv")
            self._stacked_preview.setCurrentIndex(0)
        else:
            self._l_extension.setText(".json")
            self._stacked_preview.setCurrentIndex(1)
        # プレビューを更新（既存データがあれば）
        if hasattr(self, '_current_preview_data'):
            self._update_preview(self._current_preview_data)

    def _update_preview(self, data: list[SimpleScoreExportRowDto]):
        """プレビューを更新"""
        format_enum = self.get_selected_format()

        if format_enum == ScoreExportFormat.CSV:
            # テーブルに表示
            self._table_preview.setRowCount(len(data))
            for i, row in enumerate(data):
                self._table_preview.setItem(
                    i, 0, QTableWidgetItem(str(row.student_id)))
                self._table_preview.setItem(
                    i, 1, QTableWidgetItem(row.student_name))
                score_str = str(row.score) if row.score is not None else ""
                self._table_preview.setItem(i, 2, QTableWidgetItem(score_str))
        else:
            # JSONテキストに表示
            dicts = [
                {
                    "student_id": str(r.student_id),
                    "name": r.student_name,
                    "score": r.score
                }
                for r in data
            ]
            json_text = json.dumps(dicts, ensure_ascii=False, indent=2)
            self._text_preview.setPlainText(json_text)

    def set_folder_path(self, path: str) -> None:
        """出力先フォルダパスを設定"""
        self._le_folder_path.setText(path)

    def get_folder_path(self) -> str:
        """出力先フォルダパスを取得"""
        return self._le_folder_path.text()

    def set_filename(self, name: str) -> None:
        """ファイル名を設定"""
        self._le_filename.setText(name)

    def get_filename(self) -> str:
        """ファイル名を取得"""
        return self._le_filename.text()

    def get_selected_format(self) -> ScoreExportFormat:
        """選択された形式を取得"""
        return self._cb_format.currentData()

    def set_preview_data(self, data: list[SimpleScoreExportRowDto]) -> None:
        """プレビューデータを設定"""
        self._current_preview_data = data
        self._update_preview(data)
