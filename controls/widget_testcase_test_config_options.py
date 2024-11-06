from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import QVBoxLayout, QGridLayout, QLabel, QCheckBox, QLineEdit, \
    QSpinBox, QGroupBox

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

        layout_content.addWidget(QLabel("トークンを順序通りマッチングする", self), 0, 0)

        self._cb_ordered_matching = QCheckBox(self)
        layout_content.addWidget(self._cb_ordered_matching, 0, 1)

        layout_content.addWidget(QLabel("実数をマッチングするときに許容する最大誤差", self), 1, 0)

        self._le_float_tolerance = QLineEdit(self)
        validator = QDoubleValidator(self)
        validator.setDecimals(6)
        validator.setNotation(QDoubleValidator.ScientificNotation)
        self._le_float_tolerance.setValidator(validator)
        layout_content.addWidget(self._le_float_tolerance, 1, 1)

        layout_content.addWidget(QLabel("許可する編集距離", self), 2, 0)

        self._le_allowable_edit_distance = QSpinBox(self)
        self._le_allowable_edit_distance.setMinimum(0)
        self._le_allowable_edit_distance.setMaximum(10)
        layout_content.addWidget(self._le_allowable_edit_distance, 2, 1)

        # layout_content.addWidget(QLabel("空白を無視する", self), 3, 0)
        #
        # self._cb_ignore_whitespace = QCheckBox(self)
        # layout_content.addWidget(self._cb_ignore_whitespace, 3, 1)

    def _init_signals(self):
        pass

    @pyqtSlot()
    def set_data(self, options: TestConfigOptions):
        self._cb_ordered_matching.setChecked(options.ordered_matching)
        self._le_float_tolerance.setText(f"{options.float_tolerance:.6E}")
        self._le_allowable_edit_distance.setValue(options.allowable_edit_distance)
        # self._cb_ignore_whitespace.setChecked(options.ignore_whitespace)

    @pyqtSlot()
    def get_data(self) -> TestConfigOptions:
        options = TestConfigOptions(
            ordered_matching=self._cb_ordered_matching.isChecked(),
            float_tolerance=float(self._le_float_tolerance.text()),
            allowable_edit_distance=self._le_allowable_edit_distance.value(),
            # ignore_whitespace=self._cb_ignore_whitespace.isChecked(),
        )
        return options
