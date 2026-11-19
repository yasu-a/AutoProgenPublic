from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QFrame, QWidget

from autoprogen.control.widget_error_action import ErrorActionWidget
from autoprogen.control.widget_error_extension import ErrorExtensionWidget


class SubmissionFileRecoveryWidget(ErrorExtensionWidget):
    """提出ファイルの確認と0点・一括採点除外の操作を表示する。"""

    submission_view_requested = pyqtSignal(name="submission_view_requested")
    exclusion_requested = pyqtSignal(name="exclusion_requested")

    def __init__(
            self,
            parent: QWidget = None,
            *,
            can_exclude: bool,
            already_excluded: bool,
    ) -> None:
        """実行状態と既存の除外状態に応じて二つの処置を構成する。"""
        super().__init__(parent)
        layout = self.content_layout

        self._submission_action = ErrorActionWidget(
            self,
            message=(
                "1. 提出フォルダを開いて内容を確認してください。\n"
                "修正できた場合は、メイン画面の「実行」から再実行してください。"
            ),
            button_text="提出フォルダを開く",
            button_object_name="openSubmissionFolder",
        )
        self._submission_action.action_requested.connect(
            self.submission_view_requested.emit,
        )
        self._submission_action.button.setEnabled(can_exclude)
        self._view_submission_button = self._submission_action.button
        layout.addWidget(self._submission_action)

        separator = QFrame(self)
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)

        self._exclusion_action = ErrorActionWidget(
            self,
            message=(
                "2. 確認しても対処できない場合は、0点として保存し、"
                "一括採点から除外できます。"
            ),
            button_text="0点にして一括採点から除外",
            button_object_name="excludeSubmissionFileErrorStudent",
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
                "処理中は点数と除外設定を変更できません。",
                enabled=False,
            )
        else:
            self._exclude_button.setEnabled(True)

    def set_exclusion_state(self, message: str, *, enabled: bool) -> None:
        """処置の案内文と除外ボタンの有効状態を更新する。"""
        self._exclusion_action.set_state(message, enabled=enabled)

    def _request_exclusion(self) -> None:
        """操作可能な場合だけ0点・除外要求を通知する。"""
        if self._exclude_button.isEnabled():
            self.exclusion_requested.emit()
