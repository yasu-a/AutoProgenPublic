from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QSpinBox, QLabel


class CompilerTimeoutWidget(QWidget):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout()
        self.setLayout(layout)

        self._sb_value = QSpinBox(self)
        self._sb_value.setMinimum(1)
        self._sb_value.setMaximum(120)
        self._sb_value.setSingleStep(1)
        self._sb_value.setFixedWidth(100)
        layout.addWidget(self._sb_value)

        layout.addWidget(QLabel("秒", self))

        layout.addStretch(1)

    def set_value(self, timeout: int) -> None:
        self._sb_value.setValue(timeout)

    def get_value(self) -> int:
        return self._sb_value.value()

    # noinspection PyMethodMayBeStatic
    def validate_and_get_reason(self) -> str | None:
        return None
