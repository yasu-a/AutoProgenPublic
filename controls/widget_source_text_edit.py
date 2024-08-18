import codecs
import sys

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from controls.mixin_shift_horizontal_scroll import HorizontalScrollWithShiftAndWheelMixin
from fonts import font


# https://github.com/baoboa/pyqt5/blob/master/examples/richtext/syntaxhighlighter.py
class _CHighlighter(QSyntaxHighlighter):
    TYPE_KEYWORDS = [
        "void", "char", "short", "int", "long", "float", "double", "signed", "unsigned", "_Bool",
        "_Complex", "_Imaginary", "size_t", "wchar_t", "int8_t", "int16_t", "int32_t", "int64_t",
        "uint8_t", "uint16_t", "uint32_t", "uint64_t", "int_least8_t", "int_least16_t",
        "int_least32_t", "int_least64_t", "uint_least8_t", "uint_least16_t", "uint_least32_t",
        "uint_least64_t", "int_fast8_t", "int_fast16_t", "int_fast32_t", "int_fast64_t",
        "uint_fast8_t", "uint_fast16_t", "uint_fast32_t", "uint_fast64_t", "intptr_t", "uintptr_t",
        "intmax_t", "uintmax_t",
    ]

    KEYWORDS = [
        "auto", "break", "case", "const", "continue", "default", "do", "else", "enum",
        "extern", "for", "goto", "if", "register", "return", "sizeof", "static", "struct",
        "switch", "typedef", "union", "volatile", "while",
    ]

    # noinspection SpellCheckingInspection
    FUNCTION_NAMES = [
        "malloc", "calloc", "ealloc", "free", "atoi", "atol", "atof", "rand", "rand",
        "exit", "abort", "ystem", "printf", "canf", "fprintf", "fscanf", "puts",
        "gets", "fputs", "fgets", "fopen", "fclose", "freopen", "emove", "ename",
        "fflush", "etbuf", "etvbuf", "ewind", "fseek", "ftell", "fgetpos", "fsetpos",
        "trcpy", "trncpy", "trcat", "trncat", "trcmp", "trncmp", "trcoll", "trchr",
        "trrchr", "trstr", "trpbrk", "trlen", "trspn", "trcspn", "trtok", "emset",
        "emcpy", "emmove", "emchr", "emcmp", "time", "difftime", "ktime", "localtime",
        "gmtime", "asctime", "ctime", "trftime", "trptime", "clock", "clock_gettime",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(Qt.darkBlue)
        keyword_format.setFontWeight(QFont.Bold)

        self.highlighting_rules = [
            (QRegExp(fr"\b{pattern}\b"), keyword_format)
            for pattern in self.TYPE_KEYWORDS + self.KEYWORDS + self.FUNCTION_NAMES
        ]

        preprocessor_format = QTextCharFormat()
        preprocessor_format.setForeground(Qt.darkMagenta)
        self.highlighting_rules.append((QRegExp("#.*"), preprocessor_format))

        single_line_comment_format = QTextCharFormat()
        single_line_comment_format.setForeground(Qt.red)
        self.highlighting_rules.append((QRegExp("//[^\n]*"), single_line_comment_format))

        self.multi_line_comment_format = QTextCharFormat()
        self.multi_line_comment_format.setForeground(Qt.red)

        quotation_format = QTextCharFormat()
        quotation_format.setForeground(Qt.darkGreen)
        self.highlighting_rules.append((QRegExp("\".*\""), quotation_format))

        function_format = QTextCharFormat()
        function_format.setForeground(Qt.blue)
        self.highlighting_rules.append((QRegExp("\\b[A-Za-z0-9_]+(?=\\()"), function_format))

        self.comment_start_expression = QRegExp("/\\*")
        self.comment_end_expression = QRegExp("\\*/")

    def highlightBlock(self, text, **kwargs):
        for expression, fmt in self.highlighting_rules:
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, fmt)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)

        start_index = 0
        if self.previousBlockState() != 1:
            start_index = self.comment_start_expression.indexIn(text)

        while start_index >= 0:
            end_index = self.comment_end_expression.indexIn(text, start_index)

            if end_index == -1:
                self.setCurrentBlockState(1)
                comment_length = len(text) - start_index
            else:
                comment_length = end_index - start_index + self.comment_end_expression.matchedLength()

            self.setFormat(start_index, comment_length, self.multi_line_comment_format)
            start_index = self.comment_start_expression.indexIn(text, start_index + comment_length)


class SourceTextEdit(QPlainTextEdit, HorizontalScrollWithShiftAndWheelMixin):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()

    def _init_ui(self):
        self.setFont(font(monospace=True, small=True))
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self._h = _CHighlighter(self.document())


class _TestWidget(QWidget, QObject):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        te = SourceTextEdit(self)
        with codecs.open("../vctest/test.c", "r", "utf-8") as f:
            te.setPlainText(f.read())
        layout.addWidget(te)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    # noinspection PyArgumentList
    app.setFont(font())
    w = _TestWidget()
    # noinspection PyUnresolvedReferences
    w.show()
    app.exec()
