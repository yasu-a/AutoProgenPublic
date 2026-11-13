"""安全性チェックの検出内容とソース単位の許可操作を表示する。"""

import hashlib

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QTextCursor, QTextFormat
from PyQt5.QtWidgets import (
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from autoprogen.control.student_error_detail_parser import SourceSafetyErrorDetails
from autoprogen.control.widget_source_code_text_edit import SourceCodeTextEdit


class SourceSafetyErrorWidget(QWidget):
    """安全性チェックの検出内容を表示し、許可操作を外部へ通知する。"""

    approval_requested = pyqtSignal(name="approval_requested")

    def __init__(
            self,
            parent: QWidget = None,
            *,
            source_code_text: str | None,
            safety_error: SourceSafetyErrorDetails,
            show_editing_symbols: bool,
            enable_line_wrap: bool,
            can_approve: bool = True,
            already_approved: bool = False,
    ) -> None:
        """表示対象のソース、検出情報、表示状態を設定する。"""
        super().__init__(parent)
        self._source_code_text = source_code_text
        self._safety_error = safety_error
        self._can_approve = can_approve
        self._already_approved = already_approved

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("問題が検出されたソースコード", self))
        self._source_view = SourceCodeTextEdit(self)
        self._source_view.setObjectName("sourceSafetySourceCode")
        self._source_view.setMinimumHeight(230)
        self._source_view.setReadOnly(True)
        self._source_view.set_show_editing_symbols(show_editing_symbols)
        self._source_view.set_line_wrap(enable_line_wrap)
        self._source_view.setPlainText(source_code_text or "")
        self._source_view.setEnabled(source_code_text is not None)
        layout.addWidget(self._source_view, 1)
        self._highlight_lines(safety_error.line_numbers)

        self._status_label = QLabel(self)
        self._status_label.setObjectName("sourceSafetyStatus")
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)
        self._approve_button = QPushButton("このソースコードを許可", self)
        self._approve_button.setObjectName("approveSourceSafetySkip")
        self._approve_button.clicked.connect(self._request_approval)
        layout.addWidget(self._approve_button, 0, Qt.AlignRight)
        self._update_approval_state()

    @staticmethod
    def _hash_source(source_code_text: str | None) -> str | None:
        """BUILDで保存したUTF-8のソースを、COMPILEと同じバイト列へ戻す。"""
        if source_code_text is None:
            return None
        return hashlib.sha256(source_code_text.encode("utf-8")).hexdigest()

    def _highlight_lines(self, line_numbers: tuple[int, ...]) -> None:
        """検出行全体の背景を黄色にし、最初の検出行を中央へ表示する。"""
        selections: list[QTextEdit.ExtraSelection] = []
        document = self._source_view.document()
        for line_number in sorted(set(line_numbers)):
            block = document.findBlockByNumber(line_number - 1)
            if not block.isValid():
                continue
            selection = QTextEdit.ExtraSelection()
            selection.cursor = QTextCursor(block)
            selection.format.setBackground(QColor("#fff0a6"))
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selections.append(selection)
        self._source_view.setExtraSelections(selections)
        if selections:
            self._source_view.setTextCursor(selections[0].cursor)
            self._source_view.centerCursor()

    def _update_approval_state(self) -> None:
        """検査対象の一致と既存の許可情報に基づきボタンを切り替える。"""
        expected_sha = self._safety_error.source_sha256
        current_sha = self._hash_source(self._source_code_text)
        if self._source_code_text is None:
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
        self._status_label.setText(message)
        self._approve_button.setEnabled(False)

    def set_approval_state(self, message: str, *, enabled: bool) -> None:
        """許可操作の案内文とボタンの有効状態を更新する。"""
        self._status_label.setText(message)
        self._approve_button.setEnabled(enabled)

    def _request_approval(self) -> None:
        """許可可能な状態でボタンが押されたことを外部へ通知する。"""
        if not self._approve_button.isEnabled():
            return
        self.approval_requested.emit()
