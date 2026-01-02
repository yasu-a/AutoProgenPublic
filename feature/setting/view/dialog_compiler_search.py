from pathlib import Path

from PyQt5.QtCore import QObject
from PyQt5.QtGui import QCloseEvent, QShowEvent
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QMessageBox, QInputDialog

from feature.setting.handler.interface import ICompilerSearchView, \
    ICompilerSearchHandler
from feature.setting.view.widget_compiler_search_progress import CompilerSearchProgressWidget


class CompilerSearchDialog(QDialog, ICompilerSearchView):
    """
    コンパイラ検索ダイアログ
    Handlerパターンを使用してロジックを分離
    """

    def __init__(
            self,
            parent: QObject = None,
            *,
            handler: ICompilerSearchHandler,
    ):
        super().__init__(parent)
        self._handler = handler

        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("開発者ツールの自動検索")
        self.setModal(True)
        self.setFixedSize(1300, 100)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self._w_progress = CompilerSearchProgressWidget(self)
        layout.addWidget(self._w_progress)

    def showEvent(self, evt: QShowEvent):
        """ダイアログ表示時にHandlerに通知（検索開始）"""
        super().showEvent(evt)
        self._handler.on_view_initialized()

    def closeEvent(self, evt: QCloseEvent):
        """ダイアログが閉じられようとしたとき（検索の停止）"""
        self._handler.on_close_requested()
        evt.accept()

    # ===== ICompilerSearchView実装 =====

    def set_progress_text(self, text: str) -> None:
        """進捗テキストを設定"""
        self._w_progress.set_progress_text(text)

    def show_path_selection(self, paths: list[Path]) -> Path | None:
        """パス選択を表示（戻り値: 選択されたパス、キャンセル時はNone）"""
        path_str_chosen, ok = QInputDialog.getItem(
            self,
            "開発者ツールの自動検索",
            "以下のパスが見つかりました。使用するパスを選択してください。",
            list(map(str, paths)),
            editable=False,
        )
        if ok:
            return Path(path_str_chosen)
        return None

    def show_not_found_message(self) -> None:
        """パスが見つからなかったメッセージを表示"""
        QMessageBox.warning(
            self,
            "開発者ツールの自動検索",
            "VsDevCmd.batが見つかりませんでした。手動で指定してください。",
        )

    def accept_dialog(self) -> None:
        """ダイアログをAcceptして閉じる"""
        self.accept()
        self.close()

    def get_parent_widget(self):
        """親ウィジェットを取得（QObjectのparent用）"""
        return self
