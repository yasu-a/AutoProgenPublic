from PyQt5.QtCore import QObject, QTimer, pyqtSlot
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel

from application.dependency.usecases import get_resource_usage_get_usecase
from usecases.dto.resource_usage import ResourceUsageGetResult


class ProcessResourceUsageStatusBarWidget(QWidget):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._timer = QTimer(self)
        self._timer.setInterval(1000)

        self._init_ui()
        self._init_signals()

        self._timer.start()

    def _init_ui(self):
        # noinspection PyUnresolvedReferences
        self.setStyleSheet(
            "QLabel {"
            "   color: black;"
            "   background-color: #ffffff;"
            "   border-radius: 4px;"
            "   padding: 2px;"
            "}"
        )

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self._l_disk_read_count = QLabel(self)
        layout.addWidget(self._l_disk_read_count)

        self._l_disk_write_count = QLabel(self)
        layout.addWidget(self._l_disk_write_count)

        self._l_cpu_percent = QLabel(self)
        layout.addWidget(self._l_cpu_percent)

        self._l_memory = QLabel(self)
        layout.addWidget(self._l_memory)

    def _init_signals(self):
        # noinspection PyUnresolvedReferences
        self._timer.timeout.connect(self.__timer_timeout)

    @pyqtSlot()
    def __timer_timeout(self):
        result: ResourceUsageGetResult = get_resource_usage_get_usecase().execute()
        self._l_cpu_percent.setText(f"CPU: {result.cpu_percent}%")
        self._l_memory.setText(f"RAM: {result.memory_mega_bytes:,} MB")
        self._l_disk_read_count.setText(f"Disk read: {result.disk_read_count:,}")
        self._l_disk_write_count.setText(f"Disk write: {result.disk_write_count:,}")
