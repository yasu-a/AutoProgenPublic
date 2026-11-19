from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget

from autoprogen.control.widget_error_action import ErrorActionWidget
from autoprogen.control.widget_error_extension import ErrorExtensionWidget


class NotSubmittedErrorWidget(ErrorExtensionWidget):
    """未提出学生を0点にして一括採点から除外する操作を表示する。"""

    exclusion_requested = pyqtSignal(name="exclusion_requested")

    def __init__(
            self,
            parent: QWidget = None,
            *,
            can_exclude: bool,
            already_excluded: bool,
    ) -> None:
        """実行状態と既存の除外状態に応じて処置の可否を設定する。"""
        super().__init__(parent)
        layout = self.content_layout

        self._exclusion_action = ErrorActionWidget(
            self,
            message=(
                "未提出の学生を0点として保存し、"
                "一括採点から除外します。"
            ),
            button_text="0点にして一括採点から除外",
            button_object_name="excludeNotSubmittedStudent",
        )
        self._exclusion_action.action_requested.connect(
            self._request_exclusion,
        )
        self._exclude_button = self._exclusion_action.button
        self._status_label = self._exclusion_action.message_label
        layout.addWidget(self._exclusion_action)

        if already_excluded:
            self.set_exclusion_state(
                "この学生はすでに一括採点から除外されています。\n"
                "再び採点するにはプロジェクト設定から除外設定を解除してください。",
                enabled=False,
            )
        elif not can_exclude:
            self.set_exclusion_state(
                "実行中は点数と除外設定を変更できません。",
                enabled=False,
            )
        else:
            self._exclude_button.setEnabled(True)

    def set_exclusion_state(self, message: str, *, enabled: bool) -> None:
        """処置の案内文と除外ボタンの有効状態を更新する。"""
        self._exclusion_action.set_state(message, enabled=enabled)

    def _request_exclusion(self) -> None:
        """操作可能な場合だけ除外要求を通知する。"""
        if self._exclude_button.isEnabled():
            self.exclusion_requested.emit()
