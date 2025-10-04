from PyQt5.QtCore import QObject
from PyQt5.QtGui import QTextCharFormat, QColor, QTextCursor

from application.dependency.usecase import get_global_settings_get_usecase
from control.widget_plain_text_edit import PlainTextEdit
from domain.model.output_file_test_result import MatchedToken
from res.font import get_font


class TestCaseResultOutputFileTextView(PlainTextEdit):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        self.setFont(get_font(monospace=True, small=True))
        self.set_show_editing_symbols(
            get_global_settings_get_usecase().execute().show_editing_symbols_in_stream_content,
        )
        self.set_line_wrap(
            get_global_settings_get_usecase().execute().enable_line_wrap_in_stream_content,
        )
        self.setReadOnly(True)

    def _init_signals(self):
        pass

    def set_data(
            self,
            source_code_text: str | None,
            matched_tokens: list[MatchedToken] | None,  # ハイライトしない場合はNone
    ):
        if source_code_text is None:
            self.setEnabled(False)
            self.setPlainText("")
        else:
            self.setEnabled(True)
            self.setPlainText(source_code_text)

        # ハイライトする
        if matched_tokens:
            self.blockSignals(True)

            fmt_expected = QTextCharFormat()
            fmt_expected.setBackground(QColor("lightgreen"))

            fmt_unexpected = QTextCharFormat()
            fmt_unexpected.setBackground(QColor("lightcoral"))

            for token in matched_tokens:
                # テキスト中の該当箇所を選択する
                cursor = self.textCursor()
                cursor.clearSelection()
                cursor.setPosition(
                    token.begin,
                    QTextCursor.MoveAnchor,
                )
                cursor.movePosition(
                    QTextCursor.Right,
                    QTextCursor.KeepAnchor,
                    token.end - token.begin,
                )
                # 選択範囲を塗りつぶす
                if token.pattern.is_expected:
                    cursor.setCharFormat(fmt_expected)
                else:
                    cursor.setCharFormat(fmt_unexpected)

            self.blockSignals(False)

    def get_data(self) -> str | None:
        if self.isEnabled():
            return self.toPlainText()
        else:
            return None
