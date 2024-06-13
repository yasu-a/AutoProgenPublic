from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from fonts import font


class TestCaseTextEdit(QPlainTextEdit):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self.__init_ui()
        self.__init_signals()

    def __init_ui(self):
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setFont(font(monospace=True))
        self.set_show_editing_symbols(True)

    def set_show_editing_symbols(self, v: bool):
        if v:
            option = QTextOption()
            option.setFlags(
                QTextOption.ShowTabsAndSpaces | QTextOption.ShowLineAndParagraphSeparators
            )
            self.document().setDefaultTextOption(option)
        else:
            self.document().setDefaultTextOption(QTextOption())

    def __init_signals(self):
        pass

    # https://stackoverflow.com/questions/38234021/horizontal-scroll-on-wheelevent-with-shift-too-fast
    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() == Qt.ShiftModifier:
            scrollbar = self.horizontalScrollBar()
        else:
            scrollbar = self.verticalScrollBar()

        action = QAbstractSlider.SliderSingleStepAdd
        if event.angleDelta().y() > 0:
            action = QAbstractSlider.SliderSingleStepSub

        for _ in range(6):
            scrollbar.triggerAction(action)
