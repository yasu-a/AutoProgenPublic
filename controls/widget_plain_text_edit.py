from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from controls.mixin_shift_horizontal_scroll import HorizontalScrollWithShiftAndWheelMixin
from controls.res.fonts import get_font


class PlainTextEdit(QPlainTextEdit, HorizontalScrollWithShiftAndWheelMixin):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        self.setFont(get_font(monospace=True, small=True))
        self.set_show_editing_symbols(True)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)

    def set_show_editing_symbols(self, v: bool):
        if v:
            option = QTextOption()
            option.setFlags(
                QTextOption.ShowTabsAndSpaces | QTextOption.ShowLineAndParagraphSeparators
            )
            self.document().setDefaultTextOption(option)
        else:
            self.document().setDefaultTextOption(QTextOption())

    def _init_signals(self):
        pass

