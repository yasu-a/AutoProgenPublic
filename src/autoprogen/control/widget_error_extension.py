"""エラー詳細画面の追加Widgetに共通する表示構造を提供する。"""

from PyQt5.QtWidgets import QFrame, QVBoxLayout, QWidget


class ErrorExtensionWidget(QFrame):
    """エラー詳細画面の追加Widgetに共通する枠とレイアウトを提供する。"""

    def __init__(self, parent: QWidget = None) -> None:
        """共通の枠線、余白、Widget間隔を設定する。"""
        super().__init__(parent)
        self.setObjectName("errorExtensionFrame")
        self.setStyleSheet(
            "QFrame#errorExtensionFrame {"
            "border: 1px solid #a0a0a0;"
            "border-radius: 4px;"
            "}"
        )
        self._content_layout = QVBoxLayout(self)
        self._content_layout.setContentsMargins(10, 10, 10, 10)
        self._content_layout.setSpacing(8)

    @property
    def content_layout(self) -> QVBoxLayout:
        """各Extensionが内容を追加する共通レイアウトを返す。"""
        return self._content_layout
