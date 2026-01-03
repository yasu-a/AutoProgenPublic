from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from shared.view.mixin_shift_horizontal_scroll import HorizontalScrollWithShiftAndWheelMixin
from shared.view.style.font import get_font


class PlainTextEdit(QPlainTextEdit, HorizontalScrollWithShiftAndWheelMixin):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()

    def _init_ui(self):
        self.setFont(get_font(monospace=True, small=True))

    def set_show_editing_symbols(self, v: bool):
        if v:
            option = QTextOption()
            option.setFlags(
                QTextOption.ShowTabsAndSpaces | QTextOption.ShowLineAndParagraphSeparators
            )
            self.document().setDefaultTextOption(option)
        else:
            self.document().setDefaultTextOption(QTextOption())

    def set_line_wrap(self, v: bool):
        if v:
            self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)  # type: ignore
            self.setWordWrapMode(QTextOption.WrapAnywhere)
        else:
            self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)  # type: ignore
            self.setWordWrapMode(QTextOption.NoWrap)
