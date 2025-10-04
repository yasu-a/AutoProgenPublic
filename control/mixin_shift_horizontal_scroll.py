from PyQt5.QtCore import Qt
from PyQt5.QtGui import QWheelEvent
from PyQt5.QtWidgets import QAbstractScrollArea, QAbstractSlider


class HorizontalScrollWithShiftAndWheelMixin(QAbstractScrollArea):
    # https://stackoverflow.com/questions/38234021/horizontal-scroll-on-wheelevent-with-shift-too-fast
    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() == Qt.ShiftModifier:
            scrollbar = self.horizontalScrollBar()
        else:
            scrollbar = self.verticalScrollBar()

        action = QAbstractSlider.SliderSingleStepAdd
        if event.angleDelta().y() > 0:
            action = QAbstractSlider.SliderSingleStepSub

        for _ in range(6):
            scrollbar.triggerAction(action)
