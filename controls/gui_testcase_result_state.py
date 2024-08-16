import sys

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from domain.models.testcase import TestCaseResultState
from fonts import font


class TestCaseResultStateIndicatorWidget(QFrame):
    def __init__(self, value: TestCaseResultState | None = None, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()

        self.__value = value
        self._update_value()

    def _init_ui(self):
        self.setFixedSize(QSize(50, 25))
        self.setFrameStyle(QFrame.Plain | QFrame.Panel)
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

    def _set_text_and_color(self, text: str | None, color: str | None):
        if text is None:
            self._l_text.setText("--")
        else:
            self._l_text.setText(text)
        if color is not None:
            self._l_indicator.setStyleSheet(f"background-color: {color}")

    def _update_value(self):
        if self.__value is None:
            self._set_text_and_color(None, None)
        else:
            if self.__value == TestCaseResultState.OK:
                # noinspection SpellCheckingInspection
                self._set_text_and_color(
                    text=self.__value.value,
                    color="#44ffbb",
                )
            elif self.__value == TestCaseResultState.WRONG_ANSWER:
                self._set_text_and_color(
                    text=self.__value.value,
                    color="red",
                )
            elif self.__value == TestCaseResultState.EXECUTION_TIMEOUT:
                self._set_text_and_color(
                    text=self.__value.value,
                    color="orange",
                )
            elif self.__value == TestCaseResultState.NO_BUILD_FOUND:
                self._set_text_and_color(
                    text=self.__value.value,
                    color="gray",
                )
            else:
                assert False, self.__value

    def set_value(self, value: TestCaseResultState | None):
        self.__value = value
        self._update_value()


class _TestWidget(QWidget, QObject):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout()
        self.setLayout(layout)

        layout.addWidget(
            TestCaseResultStateIndicatorWidget(
                value=None,
                parent=self,
            )
        )
        layout.addWidget(
            TestCaseResultStateIndicatorWidget(
                value=TestCaseResultState.OK,
                parent=self,
            )
        )
        layout.addWidget(
            TestCaseResultStateIndicatorWidget(
                value=TestCaseResultState.NO_BUILD_FOUND,
                parent=self,
            )
        )
        layout.addWidget(
            TestCaseResultStateIndicatorWidget(
                value=TestCaseResultState.WRONG_ANSWER,
                parent=self,
            )
        )
        layout.addWidget(
            TestCaseResultStateIndicatorWidget(
                value=TestCaseResultState.EXECUTION_TIMEOUT,
                parent=self,
            )
        )


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    # noinspection PyArgumentList
    app.setFont(font())
    w = _TestWidget()
    # noinspection PyUnresolvedReferences
    w.show()
    app.exec()
