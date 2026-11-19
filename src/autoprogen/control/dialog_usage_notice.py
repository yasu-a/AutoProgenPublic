from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from autoprogen.control.widget_usage_notice import UsageNoticeWidget
from autoprogen.res.font import get_font


class UsageNoticeDialog(QDialog):
    """使用上の注意事項を確認し、プロジェクトを開くか判断する。"""

    def __init__(
            self,
            parent: QWidget | None = None,
            *,
            app_version_text: str,
    ) -> None:
        """対象バージョンの注意事項と確認ボタンを構築する。"""
        super().__init__(parent)

        self._init_ui(app_version_text=app_version_text)
        self._init_signals()

    def _init_ui(self, *, app_version_text: str) -> None:
        """注意事項Widgetと判断用ボタンを配置する。"""
        self.setWindowTitle("使用上の注意事項")
        self.setModal(True)
        self.setMinimumWidth(720)

        layout_root = QVBoxLayout(self)

        self._notice_widget = UsageNoticeWidget(
            self,
            app_version_text=app_version_text,
        )
        layout_root.addWidget(self._notice_widget)

        layout_bottom = QHBoxLayout()
        layout_root.addLayout(layout_bottom)

        label_redisplay = QLabel(
            "この確認は、同じアプリケーションバージョンでは次回から表示されません。",
            self,
        )
        label_redisplay.setFont(get_font(small=True))
        layout_bottom.addWidget(label_redisplay)
        layout_bottom.addStretch(1)

        self._buttons = QDialogButtonBox(self)
        self._reject_button = self._buttons.addButton(
            "拒否して戻る",
            QDialogButtonBox.RejectRole,
        )
        self._accept_button = self._buttons.addButton(
            "確認して開く",
            QDialogButtonBox.AcceptRole,
        )
        self._accept_button.setObjectName("acceptUsageNotice")
        self._accept_button.setEnabled(False)
        self._reject_button.setObjectName("rejectUsageNotice")
        layout_bottom.addWidget(self._buttons)

    def _init_signals(self) -> None:
        """確認状態とダイアログの終了操作を接続する。"""
        self._notice_widget.confirmation_changed.connect(
            self._accept_button.setEnabled,
        )
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)

    @property
    def notice_widget(self) -> UsageNoticeWidget:
        """ダイアログに表示している注意事項Widgetを返す。"""
        return self._notice_widget
