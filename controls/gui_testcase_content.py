import copy

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from controls.gui_testcase_config import TestCaseConfigEditWidget
from controls.widget_plain_text_edit import PlainTextEdit
from domain.models.testcase import TestCase
from fonts import font


class TestCaseContentTextEditWidget(QWidget):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self.__init_signals()

    def _init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        layout_grid = QGridLayout()
        layout_grid.setContentsMargins(0, 0, 0, 0)
        layout_grid.setSpacing(3)
        layout.addLayout(layout_grid)

        if "title":
            label = QLabel("検証する入力", self)
            label.setAlignment(Qt.AlignHCenter)
            layout_grid.addWidget(label, 0, 0)

            label = QLabel("", self)
            label.setAlignment(Qt.AlignHCenter)
            layout_grid.addWidget(label, 0, 1)

            label = QLabel("期待する出力", self)
            label.setAlignment(Qt.AlignHCenter)
            layout_grid.addWidget(label, 0, 2)

        if "text-edit":
            self._te_input = PlainTextEdit(self)  # type: ignore
            self._te_input.setFont(font(monospace=True))
            layout_grid.addWidget(self._te_input, 1, 0)

            label = QLabel("▷", self)
            layout_grid.addWidget(label, 1, 1)

            self._te_output = PlainTextEdit(self)  # type: ignore
            self._te_output.setFont(font(monospace=True))
            layout_grid.addWidget(self._te_output, 1, 2)

        if "bottom":
            layout_v = QHBoxLayout()
            layout_grid.addLayout(layout_v, 2, 0, 2, 3)

            layout_v.addStretch(1)

            self._cb_show_editing_symbols = QCheckBox(
                "編集記号を表示（推奨）",
                self,
            )
            self._cb_show_editing_symbols.setChecked(True)
            layout_v.addWidget(self._cb_show_editing_symbols)

    def __init_signals(self):
        # noinspection PyUnresolvedReferences
        self._cb_show_editing_symbols.stateChanged.connect(self.__show_editing_symbols_changed)

    def __show_editing_symbols_changed(self):
        state = self._cb_show_editing_symbols.isChecked()
        self._te_input.set_show_editing_symbols(state)
        self._te_output.set_show_editing_symbols(state)

    def set_input_text(self, text: str):
        self._te_input.setPlainText(text)

    def get_input_text(self):
        return self._te_input.toPlainText()

    def set_output_text(self, text: str):
        self._te_output.setPlainText(text)

    def get_output_text(self):
        return self._te_output.toPlainText()


class TestCaseContentEditDialog(QDialog):
    def __init__(self, testcase: TestCase, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self.__init_signals()

        self.__testcase = testcase
        self.__set_testcase(testcase)

    def _init_ui(self):
        self.setWindowTitle("テストケースの編集")
        self.setModal(True)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self._w_text_edit = TestCaseContentTextEditWidget(self)  # type: ignore
        layout.addWidget(self._w_text_edit)

        self._w_config_edit = TestCaseConfigEditWidget(self)  # type: ignore
        layout.addWidget(self._w_config_edit)

    def __init_signals(self):
        pass

    def __set_testcase(self, testcase: TestCase):
        self._w_text_edit.set_input_text(testcase.expected_input)
        self._w_text_edit.set_output_text(testcase.expected_output)
        self._w_config_edit.set_fields_with_testcase_config(testcase.config)
        self.__testcase = testcase

    def get_testcase(self) -> TestCase:
        testcase = copy.deepcopy(self.__testcase)
        testcase.expected_input = self._w_text_edit.get_input_text()
        testcase.expected_output = self._w_text_edit.get_output_text()
        testcase.config = self._w_config_edit.get_testcase_config_from_fields()
        return testcase
