from collections.abc import Sequence

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QPlainTextEdit,
    QVBoxLayout,
)

from autoprogen.domain.model.value import StudentID
from autoprogen.usecase.dto.student_table_cell_data import StudentErrorCellDataTextEntry


class StudentErrorDetailDialog(QDialog):
    """StudentTableのエラー欄から開く、閲覧専用の詳細ダイアログ。"""

    def __init__(
            self,
            parent: QObject = None,
            *,
            student_id: StudentID,
            error_entries: Sequence[StudentErrorCellDataTextEntry],
    ) -> None:
        """学生の識別子と表示対象のエラーを受け取る。"""
        super().__init__(parent)
        self.setWindowTitle(f"エラーの詳細 - {student_id}")
        self.setModal(True)
        self.resize(850, 550)

        layout = QVBoxLayout(self)
        self._message_edit = QPlainTextEdit(self)
        self._message_edit.setReadOnly(True)
        layout.addWidget(self._message_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Close, parent=self)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.set_data(error_entries)

    def set_data(self, error_entries: Sequence[StudentErrorCellDataTextEntry]) -> None:
        """既存の詳細メッセージを、そのまま複数件まとめて表示する。"""
        messages: list[str] = []
        for entry in error_entries:
            # 詳細文に要約が含まれていれば重複して表示しない。
            if entry.detailed_text:
                if entry.summary_text and not entry.detailed_text.startswith(entry.summary_text):
                    messages.append(f"{entry.summary_text}\n{entry.detailed_text}")
                else:
                    messages.append(entry.detailed_text)
            elif entry.summary_text:
                messages.append(entry.summary_text)
        self._message_edit.setPlainText("\n\n".join(messages))
