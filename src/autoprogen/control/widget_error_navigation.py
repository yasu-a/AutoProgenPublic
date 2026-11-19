from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QVBoxLayout, QWidget

from autoprogen.control.widget_error_action import ErrorActionWidget


class ErrorNavigationWidget(QWidget):
    """エラーの解決に必要な設定画面への案内を表示する。"""

    def __init__(
            self,
            parent: QWidget = None,
            *,
            message: str,
            button_text: str,
    ) -> None:
        """表示内容を受け取り、共通の設定画面案内UIを構築する。"""
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._action_widget = ErrorActionWidget(
            self,
            message=message,
            button_text=button_text,
            button_object_name="openErrorRecoverySettings",
        )
        self._navigation_button = self._action_widget.button
        layout.addWidget(self._action_widget)


class GlobalSettingsNavigationWidget(ErrorNavigationWidget):
    """グローバル設定画面への遷移要求を提供する。"""

    global_settings_requested = pyqtSignal(name="global_settings_requested")

    def __init__(
            self,
            parent: QWidget = None,
            *,
            message: str,
            button_text: str,
    ) -> None:
        """共通レイアウトを構築し、ボタンを遷移要求へ接続する。"""
        super().__init__(parent, message=message, button_text=button_text)
        self._action_widget.action_requested.connect(
            self.global_settings_requested.emit,
        )


class TestcaseListNavigationWidget(ErrorNavigationWidget):
    """テストケース一覧画面への遷移要求を提供する。"""

    testcase_list_requested = pyqtSignal(name="testcase_list_requested")

    def __init__(
            self,
            parent: QWidget = None,
            *,
            message: str,
            button_text: str,
    ) -> None:
        """共通レイアウトを構築し、ボタンを遷移要求へ接続する。"""
        super().__init__(parent, message=message, button_text=button_text)
        self._action_widget.action_requested.connect(
            self.testcase_list_requested.emit,
        )
