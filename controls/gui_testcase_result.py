import sys

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from controls.gui_testcase_result_state import TestCaseResultStateIndicatorWidget
from controls.widget_plain_text_edit import PlainTextEdit
from domain.models.testcase import TestCaseResultState, TestCaseResult, TestCase, TestCaseConfig
from fonts import font


class TestCaseResultWidget(QWidget):
    def __init__(self, testcase_result: TestCaseResult | None = None, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()

        self.__testcase_result = testcase_result
        self._update_data()

    def _init_ui(self):
        layout = QGridLayout()
        self.setLayout(layout)

        if "ind":
            layout_ind = QVBoxLayout()
            layout_ind.setContentsMargins(0, 0, 0, 0)
            layout_ind.setSpacing(3)
            layout.addLayout(layout_ind, 1, 3)

            layout_ind.addStretch(1)

            label = QLabel("⇔")
            label.setAlignment(Qt.AlignCenter)
            layout_ind.addWidget(label)

            # noinspection PyTypeChecker
            self._w_ind = TestCaseResultStateIndicatorWidget(parent=self)
            layout_ind.addWidget(self._w_ind)

            layout_ind.addStretch(1)

        if "inter-middle-left":
            label = QLabel("▷", self)
            label.setAlignment(Qt.AlignCenter)
            label.setFixedWidth(self._w_ind.width())
            layout.addWidget(label, 1, 1)

        if "left":
            label = QLabel("入力", self)
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label, 0, 0)

            self._te_input = PlainTextEdit(self)
            self._te_input.setReadOnly(True)
            layout.addWidget(self._te_input, 1, 0)

        if "middle":
            label = QLabel("実行結果", self)
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label, 0, 2)

            self._te_actual_output = PlainTextEdit(self)
            self._te_actual_output.setReadOnly(True)
            layout.addWidget(self._te_actual_output, 1, 2)

            label = QLabel("正解出力", self)
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label, 0, 4)

        if "right":
            self._te_expected_output = PlainTextEdit(self)
            self._te_expected_output.setReadOnly(True)
            layout.addWidget(self._te_expected_output, 1, 4)

    def _update_data(self):
        if self.__testcase_result is None:
            self._w_ind.set_value(None)
            self._te_input.setPlainText("")
            self._te_input.setEnabled(False)
            self._te_actual_output.setPlainText("")
            self._te_actual_output.setEnabled(False)
            self._te_expected_output.setPlainText("")
            self._te_expected_output.setEnabled(False)
        else:
            self._w_ind.set_value(self.__testcase_result.result_state)
            self._te_input.setPlainText(self.__testcase_result.testcase.expected_input)
            self._te_input.setEnabled(True)
            if self.__testcase_result.actual_output_lines is None:
                self._te_actual_output.setPlainText("出力データの記録がありません")
                self._te_actual_output.setEnabled(False)
            else:
                self._te_actual_output.setPlainText(self.__testcase_result.actual_output)
                self._te_actual_output.setEnabled(True)
            self._te_expected_output.setPlainText(self.__testcase_result.testcase.expected_output)
            self._te_expected_output.setEnabled(True)

    def set_testcase_result(self, testcase_result: TestCaseResult | None):
        self.__testcase_result = testcase_result
        self._update_data()

    def set_line_wrap_enabled(self, e: bool):
        if e:
            mode = QPlainTextEdit.WidgetWidth
        else:
            mode = QPlainTextEdit.NoWrap
        self._te_input.setLineWrapMode(mode)
        self._te_actual_output.setLineWrapMode(mode)
        self._te_expected_output.setLineWrapMode(mode)

    def get_line_wrap_enabled(self) -> bool:
        return self._te_input.lineWrapMode() == QPlainTextEdit.WidgetWidth


class _TestWidget(QWidget, QObject):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(
            TestCaseResultWidget(
                testcase_result=None,
                parent=self,
            )
        )

        layout.addWidget(
            TestCaseResultWidget(
                testcase_result=TestCaseResult(
                    testcase=TestCase(
                        expected_input_lines=["3", "1", "2", "3"],
                        expected_output_lines=["6", "3", "5", "9"],
                        config=TestCaseConfig.create_empty(),
                        number=2,
                    ),
                    actual_output_lines=["6", "3", "5", "9"],
                    result_state=TestCaseResultState.OK,
                ),
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
