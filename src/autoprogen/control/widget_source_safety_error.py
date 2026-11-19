"""安全性チェックの検出内容とソース単位の許可操作を表示する。"""

from collections.abc import Sequence

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QLabel,
    QWidget,
)

from autoprogen.control.widget_error_action import ErrorActionWidget
from autoprogen.control.widget_error_extension import ErrorExtensionWidget
from autoprogen.control.widget_source_code_text_edit import SourceCodeTextEdit
from autoprogen.domain.error.stage.compile import SourceSafetyViolationError
from autoprogen.domain.model.source_code import SourceCode


class SourceSafetyErrorWidget(ErrorExtensionWidget):
    """安全性チェックの検出内容を表示し、許可操作を外部へ通知する。"""

    approval_requested = pyqtSignal(name="approval_requested")

    def __init__(
            self,
            parent: QWidget = None,
            *,
            source_code: SourceCode | None,
            safety_errors: Sequence[SourceSafetyViolationError],
            show_editing_symbols: bool,
            enable_line_wrap: bool,
            can_approve: bool = True,
            already_approved: bool = False,
    ) -> None:
        """表示対象のソース、検出情報、表示状態を設定する。"""
        super().__init__(parent)
        self._source_code = source_code
        errors = tuple(safety_errors)
        source_hashes = {error.source_sha256 for error in errors}
        self._source_sha256 = (
            next(iter(source_hashes)) if len(source_hashes) == 1 else None
        )
        self._can_approve = can_approve
        self._already_approved = already_approved

        layout = self.content_layout
        layout.addWidget(QLabel("問題が検出されたソースコード", self))
        self._source_view = SourceCodeTextEdit(self)
        self._source_view.setObjectName("sourceSafetySourceCode")
        self._source_view.setMinimumHeight(230)
        self._source_view.setReadOnly(True)
        self._source_view.set_show_editing_symbols(show_editing_symbols)
        self._source_view.set_line_wrap(enable_line_wrap)
        self._source_view.setPlainText(source_code.text if source_code is not None else "")
        self._source_view.setEnabled(source_code is not None)
        layout.addWidget(self._source_view, 1)
        highlighted_lines = tuple(
            sorted({
                finding.line_number
                for error in errors
                for finding in error.findings
                if finding.line_number > 0
            })
        )
        self._source_view.set_highlighted_lines(highlighted_lines)
        if highlighted_lines:
            self._source_view.centerCursor()

        self._approval_action = ErrorActionWidget(
            self,
            message="",
            button_text="このソースコードを許可",
            button_object_name="approveSourceSafetySkip",
        )
        self._approval_action.action_requested.connect(self._request_approval)
        self._approve_button = self._approval_action.button
        self._status_label = self._approval_action.message_label
        self._status_label.setObjectName("sourceSafetyStatus")
        layout.addWidget(self._approval_action)
        self._update_approval_state()

    def _update_approval_state(self) -> None:
        """検査対象の一致と既存の許可情報に基づきボタンを切り替える。"""
        expected_sha = self._source_sha256
        current_sha = (
            self._source_code.calculate_sha256()
            if self._source_code is not None
            else None
        )
        if self._source_code is None:
            message = "ソースコードを取得できないため、許可できません。"
        elif expected_sha is None:
            message = "検査時のSHA-256が記録されていません。再実行してから許可してください。"
        elif current_sha != expected_sha:
            message = "ソースコードが検査時から変わっています。再実行してから許可してください。"
        elif not self._can_approve:
            message = "処理中はソースコードを許可できません。実行完了後に開いてください。"
        elif self._already_approved:
            message = "このソースコードはすでに許可されています。"
        else:
            self.set_approval_state(
                "この学生の同じソースコードに限り、次回の実行から安全性チェックを省略します。",
                enabled=True,
            )
            return
        self._approval_action.set_state(message, enabled=False)

    def set_approval_state(self, message: str, *, enabled: bool) -> None:
        """許可操作の案内文とボタンの有効状態を更新する。"""
        self._approval_action.set_state(message, enabled=enabled)

    def _request_approval(self) -> None:
        """許可可能な状態でボタンが押されたことを外部へ通知する。"""
        if not self._approve_button.isEnabled():
            return
        self.approval_requested.emit()
