from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QLabel


class ClickableLabelWidget(QLabel):
    clicked = pyqtSignal(name="clicked")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def mousePressEvent(self, evt: QMouseEvent):
        # noinspection PyUnresolvedReferences
        self.clicked.emit()
