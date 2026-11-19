from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget


class ErrorActionWidget(QWidget):
    """エラーへの一つの案内文と対応する操作ボタンを中央に表示する。"""

    action_requested = pyqtSignal(name="action_requested")

    def __init__(
            self,
            parent: QWidget = None,
            *,
            message: str,
            button_text: str,
            button_object_name: str,
    ) -> None:
        """折り返さない案内文と操作ボタンを共通レイアウトへ配置する。"""
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch(1)

        self._message_label = QLabel(message, self)
        self._message_label.setAlignment(Qt.AlignCenter)
        self._message_label.setWordWrap(False)
        self._message_label.setSizePolicy(
            QSizePolicy.MinimumExpanding,
            QSizePolicy.Preferred,
        )
        layout.addWidget(self._message_label, alignment=Qt.AlignCenter)

        self._button = QPushButton(button_text, self)
        self._button.setObjectName(button_object_name)
        self._button.clicked.connect(self.action_requested.emit)
        layout.addWidget(self._button, alignment=Qt.AlignCenter)
        layout.addStretch(1)

    @property
    def button(self) -> QPushButton:
        """操作可否の更新に利用するボタンを返す。"""
        return self._button

    @property
    def message_label(self) -> QLabel:
        """処置結果の表示にも利用する案内ラベルを返す。"""
        return self._message_label

    def set_state(self, message: str, *, enabled: bool) -> None:
        """案内文と操作ボタンの有効状態を更新する。"""
        self._message_label.setText(message)
        self._button.setEnabled(enabled)
