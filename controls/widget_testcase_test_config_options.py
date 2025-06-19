from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWidgets import QVBoxLayout, QGridLayout, QGroupBox, QCheckBox

from domain.models.test_config_options import TestConfigOptions


class TestCaseTestConfigOptionsEditWidget(QGroupBox):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        layout_root = QVBoxLayout()
        self.setLayout(layout_root)

        layout_content = QGridLayout()
        layout_root.addLayout(layout_content)

        self._cb_ignore_case = QCheckBox(self)
        self._cb_ignore_case.setText("大文字・小文字の違いを無視する")
        layout_content.addWidget(self._cb_ignore_case, 1, 1)

    def _init_signals(self):
        pass

    @pyqtSlot()
    def set_data(self, options: TestConfigOptions):
        self._cb_ignore_case.setChecked(options.ignore_case)

    @pyqtSlot()
    def get_data(self) -> TestConfigOptions:
        options = TestConfigOptions(
            ignore_case=self._cb_ignore_case.isChecked(),
        )
        return options
