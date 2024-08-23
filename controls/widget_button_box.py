from typing import Iterable

from PyQt5.QtCore import pyqtSignal, QObject, Qt, pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton


class ButtonBox(QWidget):
    triggered = pyqtSignal(str, name="triggered")  # command name

    def __init__(self, parent: QObject = None, *, orientation):
        super().__init__(parent)

        self._orientation = orientation

        self._init_ui()

    def _init_ui(self):
        if self._orientation == Qt.Horizontal:
            self._button_layout = QHBoxLayout()
            root_layout = QHBoxLayout()
            root_layout.addStretch(1)
            root_layout.addLayout(self._button_layout)
        elif self._orientation == Qt.Vertical:
            self._button_layout = QVBoxLayout()
            root_layout = QVBoxLayout()
            root_layout.addLayout(self._button_layout)
            root_layout.addStretch(1)
        else:
            raise ValueError("Invalid orientation", self._orientation)
        self.setLayout(root_layout)

        self.set_margins(0)

    def set_margins(self, margin: int):
        self.layout().setContentsMargins(margin, margin, margin, margin)

    def add_button(self, title: str, name: str, icon: QIcon = None):
        b = QPushButton(self)
        b.setText(title)
        if icon is not None:
            b.setIcon(icon)
        b.setObjectName(name)
        b.clicked.connect(self.__on_b_clicked)  # type: ignore
        self._button_layout.addWidget(b)

    def _iter_buttons(self) -> Iterable[QPushButton]:
        yield from self.layout().findChildren(QPushButton)

    def set_button_width(self, v):  # FIXME: not working
        for b in self._iter_buttons():
            b.setFixedWidth(v)

    def set_button_height(self, v):  # FIXME: not working
        for b in self._iter_buttons():
            b.setFixedHeight(v)

    @pyqtSlot()
    def __on_b_clicked(self):
        b = self.sender()
        command_name = b.objectName()
        # noinspection PyUnresolvedReferences
        self.triggered.emit(command_name)
