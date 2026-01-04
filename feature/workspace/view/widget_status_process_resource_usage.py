from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel

from feature.workspace.handler.interface import IProcessResourceUsageStatusBarView


class ProcessResourceUsageStatusBarWidget(QWidget, IProcessResourceUsageStatusBarView):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()

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

    # ===== IProcessResourceUsageStatusBarView実装 =====

    def set_resource_usage(self, cpu_percent: int, memory_mega_bytes: int, disk_read_count: int, disk_write_count: int) -> None:
        """リソース使用状況を設定"""
        self._l_cpu_percent.setText(f"CPU: {cpu_percent}%")
        self._l_memory.setText(f"RAM: {memory_mega_bytes:,} MB")
        self._l_disk_read_count.setText(f"Disk read: {disk_read_count:,}")
        self._l_disk_write_count.setText(f"Disk write: {disk_write_count:,}")
