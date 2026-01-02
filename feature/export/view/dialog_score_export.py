from pathlib import Path

from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLabel, \
    QVBoxLayout, QPlainTextEdit, QPushButton, QLineEdit, QComboBox, \
    QFileDialog, QMessageBox

from feature.export.handler.interface import IScoreExportDialogHandler, IScoreExportDialogView
from shared.view.style.font import get_font
from shared.view.style.icon import get_icon
from shared.view.widget_horizontal_line import HorizontalLineWidget


class ScoreExportDialog(QDialog, IScoreExportDialogView):
    def __init__(
            self,
            parent: QObject = None,
            *,
            handler: IScoreExportDialogHandler,
    ):
        super().__init__(parent)
        self._handler = handler

        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("採点結果のエクスポート")
        self.setModal(True)
        self.resize(800, 600)

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("1. エクスポート先のExcelワークブックを選択してください", self))

        layout_path = QHBoxLayout()
        layout.addLayout(layout_path)

        self._le_excel_fullpath = QLineEdit(self)
        layout_path.addWidget(self._le_excel_fullpath)

        self._b_select_excel_fullpath = QPushButton(self)
        self._b_select_excel_fullpath.setIcon(get_icon("folder"))
        self._b_select_excel_fullpath.setFixedWidth(30)
        layout_path.addWidget(self._b_select_excel_fullpath)

        self._te_message = QPlainTextEdit(self)
        self._te_message.setReadOnly(True)
        self._te_message.setEnabled(False)
        self._te_message.setFont(get_font(small=True))
        layout.addWidget(self._te_message)

        layout.addWidget(HorizontalLineWidget())

        layout.addWidget(QLabel("2. エクスポート先のワークシートを選択してください", self))

        self._dl_sheet_names = QComboBox(self)
        self._dl_sheet_names.setEnabled(False)
        layout.addWidget(self._dl_sheet_names)

        layout.addWidget(HorizontalLineWidget())

        layout.addWidget(QLabel("3. 設問番号を確認してください", self))

        self._l_target_id = QLabel(self)
        layout.addWidget(self._l_target_id)

        layout.addWidget(HorizontalLineWidget())

        layout.addWidget(QLabel("4. 書き込む", self))

        self._b_export = QPushButton("エクスポート", self)
        self._b_export.setEnabled(False)
        layout.addWidget(self._b_export)

        # シグナル接続
        # noinspection PyUnresolvedReferences
        self._le_excel_fullpath.textChanged.connect(self.__le_excel_fullpath_text_changed)
        # noinspection PyUnresolvedReferences
        self._b_select_excel_fullpath.clicked.connect(self.__b_select_excel_fullpath_clicked)
        # noinspection PyUnresolvedReferences
        self._b_export.clicked.connect(self.__b_export_clicked)

    def showEvent(self, evt) -> None:
        """ダイアログ表示時にHandlerに通知"""
        super().showEvent(evt)
        if self._handler:
            self._handler.on_view_initialized()

    @pyqtSlot()
    def __b_select_excel_fullpath_clicked(self):
        """Excelファイル選択ボタンがクリックされたとき"""
        if self._handler:
            self._handler.on_excel_path_select_requested()

    @pyqtSlot()
    def __le_excel_fullpath_text_changed(self):
        """Excelファイルパスが変更されたとき"""
        if self._handler:
            self._handler.on_excel_path_changed(self._le_excel_fullpath.text())

    @pyqtSlot()
    def __b_export_clicked(self):
        """エクスポートボタンがクリックされたとき"""
        if self._handler:
            self._handler.on_export_requested()

    # ===== IScoreExportDialogView実装 =====
    def set_excel_path(self, path: str) -> None:
        """Excelファイルパスを設定"""
        self._le_excel_fullpath.setText(path)

    def get_excel_path(self) -> str:
        """Excelファイルパスを取得"""
        return self._le_excel_fullpath.text()

    def set_worksheet_names(self, names: list[str]) -> None:
        """ワークシート名リストを設定"""
        self._dl_sheet_names.clear()
        for name in names:
            self._dl_sheet_names.addItem(name)

    def get_selected_worksheet_name(self) -> str:
        """選択中のワークシート名を取得"""
        return self._dl_sheet_names.currentText()

    def set_message(self, message: str) -> None:
        """メッセージを設定"""
        self._te_message.setPlainText(message)
        self._te_message.setEnabled(bool(message))

    def set_export_enabled(self, enabled: bool) -> None:
        """エクスポートボタンの有効/無効を設定"""
        self._b_export.setEnabled(enabled)
        self._dl_sheet_names.setEnabled(enabled)

    def set_excel_path_valid(self, valid: bool) -> None:
        """Excelファイルパスの有効性を設定（スタイル変更用）"""
        if valid:
            self._le_excel_fullpath.setStyleSheet("background-color: lightgreen")
        else:
            self._le_excel_fullpath.setStyleSheet("background-color: orange")

    def show_export_confirmation(self, message: str) -> bool:
        """エクスポート確認ダイアログを表示（戻り値: True=実行, False=キャンセル）"""
        res = QMessageBox.question(
            self,  # type: ignore
            "点数のエクスポート",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return res == QMessageBox.Yes

    def show_export_success(self, backup_path: Path | None, message: str) -> bool:
        """エクスポート成功ダイアログを表示（戻り値: True=ファイルを開く, False=閉じる）"""
        res = QMessageBox.question(
            self,  # type: ignore
            "点数のエクスポート",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if res == QMessageBox.Yes:
            self.accept()
        return res == QMessageBox.Yes

    def show_export_error(self, error_message: str) -> None:
        """エクスポートエラーダイアログを表示"""
        QMessageBox.critical(
            self,  # type: ignore
            "点数のエクスポート",
            f"エクスポートに失敗しました。\n{error_message}",
        )

    def show_file_dialog(self, default_path: Path) -> Path | None:
        """ファイル選択ダイアログを表示（戻り値: 選択されたパス、キャンセル時はNone）"""
        fullpath, _ = QFileDialog.getOpenFileName(
            self,  # type: ignore
            "エクスポート先のエクセルファイルを選択",
            str(default_path),
            "Excelファイル (*.xlsx)",
        )
        if not fullpath:
            return None
        return Path(fullpath)

    def set_target_id(self, target_id) -> None:
        """設問番号を設定（初期化時に呼ぶ）"""
        self._l_target_id.setText(f" 設問番号: {target_id}")
