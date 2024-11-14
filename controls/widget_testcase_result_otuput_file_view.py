from PyQt5.QtCore import QObject
from PyQt5.QtGui import QTextCharFormat, QColor, QTextCursor
from PyQt5.QtWidgets import QPlainTextEdit

from controls.mixin_shift_horizontal_scroll import HorizontalScrollWithShiftAndWheelMixin
from controls.res.fonts import get_font
from domain.models.test_result_output_file_entry import AbstractTestResultOutputFileEntry


class TestCaseResultOutputFileViewWidget(QPlainTextEdit, HorizontalScrollWithShiftAndWheelMixin):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._output_file_entry: AbstractTestResultOutputFileEntry | None = None

        self._show_pure_text = False

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        self.setFont(get_font(monospace=True, small=True))
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setReadOnly(True)

    def _init_signals(self):
        pass

    def __update(self):
        if self._output_file_entry is None:
            self.setPlainText("")
            self.setEnabled(False)
            return
        else:
            self.setEnabled(True)

        text_cursor_before_update = self.textCursor()

        errors = []
        content_replacement = None
        actual_content = ""
        if self._output_file_entry.has_actual:
            actual_content = self._output_file_entry.actual.content_string
            if actual_content is None:
                errors.append("⚠ 文字コードが不明です")
                actual_content = ""
                content_replacement = "（不明な文字コード）"
            elif actual_content == "":
                content_replacement = "（空）"
            else:
                pass  # 正常な出力
            if self._output_file_entry.has_expected:
                pass  # 正常な結果
            else:
                errors.append("⚠ テスト対象ではありません")
        else:
            if self._output_file_entry.has_expected:
                errors.append("⚠ プログラムから出力されませんでした")
            else:
                assert False, "unreachable"

        if self._show_pure_text:
            # エラーや代替テキストがあっても表示しない
            content_header = ""
            content_text = actual_content
        else:
            if errors:
                content_header = "\n".join(errors) + "\n\n＜ストリームの内容＞\n"
            else:
                content_header = ""
            if content_replacement is None:
                content_text = actual_content
            else:
                content_text = content_replacement

        pure_text_shown = not content_header and content_replacement is None and content_text

        self.blockSignals(True)

        # テキストをセット
        text_to_set = content_header + content_text
        if self.toPlainText() != text_to_set:
            self.setPlainText(content_header + content_text)

        # テスト結果が存在すればテキストをハイライトする
        if self._output_file_entry.has_actual and self._output_file_entry.has_expected:
            if pure_text_shown:
                test_result = self._output_file_entry.test_result

                fmt_expected = QTextCharFormat()
                fmt_expected.setBackground(QColor("lightgreen"))

                fmt_unexpected = QTextCharFormat()
                fmt_unexpected.setBackground(QColor("lightcoral"))

                for token in test_result.matched_tokens:
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

        self.textCursor().setPosition(text_cursor_before_update.position())

    def set_show_pure_text(self, v: bool):
        if self._show_pure_text != v:
            self._show_pure_text = v
            self.__update()

    def set_data(self, output_file_entry: AbstractTestResultOutputFileEntry):
        self._output_file_entry = output_file_entry
        self.__update()
