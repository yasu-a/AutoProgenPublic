from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class NotSubmittedErrorWidget(QWidget):
    """未提出学生を0点にして一括採点から除外する操作を表示する。"""

    exclusion_requested = pyqtSignal(name="exclusion_requested")

    def __init__(
            self,
            parent: QWidget = None,
            *,
            can_exclude: bool,
            already_excluded: bool,
    ) -> None:
        """実行状態と既存の除外状態に応じて操作可否を設定する。"""
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        bottom = QHBoxLayout()
        layout.addLayout(bottom)
        bottom.addStretch(1)
        self._exclude_button = QPushButton(
            "0点にして一括採点から除外",
            self,
        )
        self._exclude_button.setObjectName("excludeNotSubmittedStudent")
        self._exclude_button.clicked.connect(self._request_exclusion)
        bottom.addWidget(self._exclude_button)
        self._status_label = QLabel(self)
        self._status_label.setObjectName("notSubmittedExclusionStatus")
        bottom.addWidget(self._status_label)
        bottom.addStretch(1)

        if already_excluded:
            self.set_exclusion_state(
                "この学生はすでに一括採点から除外されています。",
                enabled=False,
            )
        elif not can_exclude:
            self.set_exclusion_state(
                "処理中は点数と除外設定を変更できません。実行完了後に開いてください。",
                enabled=False,
            )
        else:
            self.set_exclusion_state(
                "未提出の学生を0点として保存し、一括採点から除外します。",
                enabled=True,
            )

    def set_exclusion_state(self, message: str, *, enabled: bool) -> None:
        """処置の案内文とボタンの有効状態を更新する。"""
        self._status_label.setText(message)
        self._exclude_button.setEnabled(enabled)

    def _request_exclusion(self) -> None:
        """操作可能な場合だけ除外要求を通知する。"""
        if self._exclude_button.isEnabled():
            self.exclusion_requested.emit()
