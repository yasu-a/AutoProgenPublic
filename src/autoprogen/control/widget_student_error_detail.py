from collections.abc import Sequence

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QFrame, QPlainTextEdit, QSplitter, QVBoxLayout, QWidget

from autoprogen.usecase.dto.student_table_cell_data import StudentErrorCellDataTextEntry


class StudentErrorDetailWidget(QWidget):
    """学生のエラー詳細とエラー固有UIをドック内へ表示する。"""

    def __init__(
            self,
            parent: QWidget = None,
            *,
            error_entries: Sequence[StudentErrorCellDataTextEntry],
    ) -> None:
        """表示対象のエラーを受け取り、下ドック用の横レイアウトを構成する。"""
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        frame = QFrame(self)
        frame.setObjectName("studentErrorDetailFrame")
        frame.setStyleSheet(
            "#studentErrorDetailFrame { border: 1px solid #a0a0a0; border-radius: 4px; }"
        )
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(frame)

        self._splitter = QSplitter(Qt.Horizontal, frame)
        frame_layout.addWidget(self._splitter)
        self._message_edit = QPlainTextEdit(self._splitter)
        self._message_edit.setReadOnly(True)
        self._splitter.addWidget(self._message_edit)

        self._extension_container = QWidget(self._splitter)
        self._extension_container.setObjectName(
            "studentErrorExtensionContainer")
        self._extension_layout = QVBoxLayout(self._extension_container)
        self._extension_layout.setContentsMargins(0, 0, 0, 0)
        self._extension_widget: QWidget | None = None
        self._extension_container.hide()
        self._splitter.addWidget(self._extension_container)

        self.set_data(error_entries)

    def set_extension_widget(self, widget: QWidget | None) -> None:
        """エラー固有のウィジェットを差し替え、Noneなら共通表示だけに戻す。"""
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
        # 表示後に確定した横幅へ、詳細文と追加Widgetの初期比率を適用する。
        QTimer.singleShot(0, self._set_initial_splitter_sizes)

    def _set_initial_splitter_sizes(self) -> None:
        """詳細文と追加Widgetを1:2の初期比率にする。"""
        if self._extension_widget is None:
            return
        self._splitter.setSizes([1000, 2000])

    def set_data(self, error_entries: Sequence[StudentErrorCellDataTextEntry]) -> None:
        """既存の詳細メッセージを、そのまま複数件まとめて表示する。"""
        messages: list[str] = []
        for entry in error_entries:
            # 詳細文に要約が含まれていれば重複して表示しない。
            if entry.detailed_text:
                if entry.summary_text and not entry.detailed_text.startswith(entry.summary_text):
                    messages.append(
                        f"{entry.summary_text}\n{entry.detailed_text}")
                else:
                    messages.append(entry.detailed_text)
            elif entry.summary_text:
                messages.append(entry.summary_text)
        self._message_edit.setPlainText("\n\n".join(messages))
