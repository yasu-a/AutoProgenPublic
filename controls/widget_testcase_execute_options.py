from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QDoubleSpinBox

from domain.models.testcase import ExecuteConfigOptions


class TestCaseExecuteConfigOptionsEditWidget(QWidget):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        layout_root = QVBoxLayout()
        self.setLayout(layout_root)

        layout_content = QGridLayout()
        layout_root.addLayout(layout_content)

        layout_content.addWidget(QLabel("実行のタイムアウト（秒）", self), 0, 0)

        self._sb_timeout = QDoubleSpinBox(self)
        self._sb_timeout.setMinimum(0.1)
        self._sb_timeout.setMaximum(30.0)
        self._sb_timeout.setSingleStep(0.1)
        self._sb_timeout.setDecimals(1)
        layout_content.addWidget(self._sb_timeout, 0, 1)

        layout_root.addStretch(1)

    def _init_signals(self):
        pass

    @pyqtSlot()
    def set_data(self, options: ExecuteConfigOptions):
        self._sb_timeout.setValue(options.timeout)

    @pyqtSlot()
    def get_data(self) -> ExecuteConfigOptions:
        options = ExecuteConfigOptions(
            timeout=self._sb_timeout.value(),
        )
        return options
