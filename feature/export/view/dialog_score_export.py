from pathlib import Path
from typing import TYPE_CHECKING

from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtGui import QShowEvent
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QMessageBox, QTabWidget

from feature.export.handler.interface import (
    ISimpleScoreExportTabHandler,
    IExcelScoreExportTabHandler,
    ISimpleScoreExportTabView,
    IExcelScoreExportTabView,
)
from feature.export.view.component.tab_simple import SimpleScoreExportTab
from feature.export.view.component.tab_excel import ExcelScoreExportTab

if TYPE_CHECKING:
    pass


class ScoreExportDialog(
    QDialog,
    ISimpleScoreExportTabView,
    IExcelScoreExportTabView,
):
    def __init__(
            self,
            parent: QObject = None,
            *,
            simple_tab: SimpleScoreExportTab,
            excel_tab: ExcelScoreExportTab,
            simple_handler: ISimpleScoreExportTabHandler,
            excel_handler: IExcelScoreExportTabHandler,
    ):
        super().__init__(parent)
        self._simple_tab = simple_tab
        self._excel_tab = excel_tab
        self._simple_handler = simple_handler
        self._excel_handler = excel_handler

        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        self.setWindowTitle("採点結果のエクスポート")
        self.setModal(True)
        self.resize(900, 700)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # タブウィジェット
        self._tab_widget = QTabWidget(self)
        layout.addWidget(self._tab_widget)

        # 受け取ったView（タブ）を追加（Excelタブを最初に表示）
        self._tab_widget.addTab(self._excel_tab, "Excelを上書き")
        self._tab_widget.addTab(self._simple_tab, "新規ファイル作成")

        # ボタンエリア（キャンセルとエクスポート）
        layout_buttons = QHBoxLayout()
        layout.addLayout(layout_buttons)
        layout_buttons.addStretch()
        self._b_cancel = QPushButton("キャンセル", self)
        layout_buttons.addWidget(self._b_cancel)
        self._b_export = QPushButton("エクスポート", self)
        layout_buttons.addWidget(self._b_export)

    def showEvent(self, evt: QShowEvent) -> None:
        """ダイアログ表示時にHandlerに通知"""
        super().showEvent(evt)
        self._simple_handler.on_view_initialized()
        self._excel_handler.on_view_initialized()

    def _connect_signals(self):
        """シグナル接続（Viewの責務）"""
        # エクスポートボタン
        # noinspection PyUnresolvedReferences
        self._b_export.clicked.connect(self.__on_export_clicked)
        
        # キャンセルボタン
        # noinspection PyUnresolvedReferences
        self._b_cancel.clicked.connect(self.reject)
        
        # Excelタブのシグナル
        # noinspection PyUnresolvedReferences
        self._excel_tab.file_path_changed.connect(
            lambda path: self._excel_handler.on_excel_path_changed(path)
        )
        # noinspection PyUnresolvedReferences
        self._excel_tab.sheet_selection_changed.connect(
            lambda: self._excel_handler.on_excel_sheet_selection_changed()
        )
        # noinspection PyUnresolvedReferences
        self._excel_tab.mapping_changed.connect(
            lambda: self._excel_handler.on_excel_mapping_changed()
        )

    @pyqtSlot()
    def __on_export_clicked(self):
        """エクスポートボタンがクリックされたとき"""
        current_tab_index = self.get_current_tab_index()
        if current_tab_index == 0:
            self._excel_handler.on_export_requested()
        elif current_tab_index == 1:
            self._simple_handler.on_export_requested()

    def get_current_tab_index(self) -> int:
        """現在のタブインデックスを取得（0=Excel, 1=Simple）"""
        return self._tab_widget.currentIndex()

    @property
    def simple_tab(self) -> SimpleScoreExportTab:
        """SimpleScoreExportTabへのアクセサ"""
        return self._simple_tab

    @property
    def excel_tab(self) -> ExcelScoreExportTab:
        """ExcelScoreExportTabへのアクセサ"""
        return self._excel_tab

    def show_export_error(self, error_message: str) -> None:
        """エクスポートエラーダイアログを表示"""
        QMessageBox.critical(
            self,  # type: ignore
            "点数のエクスポート",
            f"エクスポートに失敗しました。\n{error_message}",
        )

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
