from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import QVBoxLayout, QGridLayout, QLabel, QLineEdit, \
    QGroupBox

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

        layout_content.addWidget(QLabel("実数をマッチングするときに許容する最大誤差", self), 1, 0)

        self._le_float_tolerance = QLineEdit(self)
        validator = QDoubleValidator(self)
        validator.setDecimals(6)
        validator.setNotation(QDoubleValidator.ScientificNotation)
        self._le_float_tolerance.setValidator(validator)
        layout_content.addWidget(self._le_float_tolerance, 1, 1)

    def _init_signals(self):
        pass

    @pyqtSlot()
    def set_data(self, options: TestConfigOptions):
        self._le_float_tolerance.setText(f"{options.float_tolerance:.6E}")

    @pyqtSlot()
    def get_data(self) -> TestConfigOptions:
        options = TestConfigOptions(
            float_tolerance=float(self._le_float_tolerance.text()),
        )
        return options
