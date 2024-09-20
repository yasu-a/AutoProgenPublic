import sys

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from domain.models.student_stage_result import TestSummary
from fonts import font


class TestCaseTestSummaryIndicatorWidget(QFrame):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()

        self.__value = None
        self._update_value()

    def _init_ui(self):
        self.setFixedSize(QSize(50, 25))
        self.setFrameStyle(QFrame.Plain | QFrame.Panel)
        # noinspection PyUnresolvedReferences
        self.setStyleSheet(
            "TestCaseResultStateIndicatorWidget { border: 1px solid black; border-radius: 5px; }"
        )

        layout = QHBoxLayout()
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(3)
        self.setLayout(layout)

        layout.addStretch(1)

        self._l_text = QLabel("", self)
        self._l_text.setFont(font(monospace=True, bold=True))
        layout.addWidget(self._l_text)

        self._l_indicator = QLabel("", self)
        self._l_indicator.setFixedSize(QSize(11, 11))
        self._l_indicator.setFont(font(monospace=True))
        layout.addWidget(self._l_indicator)

        layout.addStretch(1)

    _TEST_SUMMARY_ABBREVIATIONS = {
        TestSummary.WRONG_ANSWER: "WA",
        TestSummary.ACCEPTED: "AC",
        TestSummary.UNTESTABLE: "E",
    }

    _TEST_SUMMARY_COLORS = {
        TestSummary.WRONG_ANSWER: "red",
        TestSummary.ACCEPTED: "#44ffbb",
        TestSummary.UNTESTABLE: "orange",
    }

    def _update_value(self):
        if self.__value is None:
            self._l_text.setText("--")
            # noinspection PyUnresolvedReferences
            self._l_indicator.setStyleSheet(
                ""
            )
            # noinspection PyUnresolvedReferences
            self.setToolTip("")
        else:
            self._l_text.setText(self._TEST_SUMMARY_ABBREVIATIONS[self.__value])
            # noinspection PyUnresolvedReferences
            self._l_indicator.setStyleSheet(
                f"background-color: {self._TEST_SUMMARY_COLORS[self.__value]}"
            )
            # noinspection PyUnresolvedReferences
            self.setToolTip(self.__value.value)

    def set_data(self, value: TestSummary | None):
        self.__value = value
        self._update_value()


class _TestWidget(QWidget, QObject):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout()
        self.setLayout(layout)

        for value in [
            None,
            TestSummary.WRONG_ANSWER,
            TestSummary.ACCEPTED,
            TestSummary.UNTESTABLE,
        ]:
            widget = TestCaseTestSummaryIndicatorWidget(parent=self)
            widget.set_data(value)
            layout.addWidget(widget)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    # noinspection PyArgumentList
    app.setFont(font())
    w = _TestWidget()
    # noinspection PyUnresolvedReferences
    w.show()
    app.exec()
