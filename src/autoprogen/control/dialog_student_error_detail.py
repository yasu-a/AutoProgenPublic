from collections.abc import Sequence

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
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
        layout.addWidget(self._message_edit, 1)

        # エラーの種類に応じた専用ウィジェットを共通メッセージと閉じるボタンの間に置く。
        self._extension_container = QWidget(self)
        self._extension_container.setObjectName("studentErrorExtensionContainer")
        self._extension_layout = QVBoxLayout(self._extension_container)
        self._extension_layout.setContentsMargins(0, 0, 0, 0)
        self._extension_widget: QWidget | None = None
        self._extension_container.hide()
        layout.addWidget(self._extension_container, 2)

        buttons = QDialogButtonBox(QDialogButtonBox.Close, parent=self)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.set_data(error_entries)

    def set_extension_widget(self, widget: QWidget | None) -> None:
        """エラー固有のウィジェットを差し替える。Noneなら共通表示だけに戻す。"""
        if self._extension_widget is not None:
            self._extension_layout.removeWidget(self._extension_widget)
            self._extension_widget.setParent(None)
            self._extension_widget.deleteLater()
        self._extension_widget = widget
        if widget is None:
            self._extension_container.hide()
            return
        self._extension_layout.addWidget(widget)
        self._extension_container.show()
        self.resize(max(self.width(), 960), max(self.height(), 710))

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
