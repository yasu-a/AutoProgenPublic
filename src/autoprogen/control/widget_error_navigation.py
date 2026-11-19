"""設定画面への移動を促すエラー用の共通Widget。"""

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget

from autoprogen.control.widget_error_action import ErrorActionWidget
from autoprogen.control.widget_error_extension import ErrorExtensionWidget


class ErrorNavigationWidget(ErrorExtensionWidget):
    """表示文とボタン文言だけを変えて使う共通の画面遷移Widget。"""

    navigation_requested = pyqtSignal(name="navigation_requested")

    def __init__(
            self,
            parent: QWidget = None,
            *,
            message: str,
            button_text: str,
    ) -> None:
        """独自の画面遷移処理は持たず、押下をSignalで通知する。"""
        super().__init__(parent)
        layout = self.content_layout
        action = ErrorActionWidget(
            self,
            message=message,
            button_text=button_text,
            button_object_name="openErrorRecoverySettings",
        )
        action.action_requested.connect(self.navigation_requested.emit)
        layout.addWidget(action)
