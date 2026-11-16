from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel

from autoprogen.usecase.dto.resource_usage import ResourceUsageGetResult


class ProcessResourceUsageStatusBarWidget(QWidget):
    """渡されたプロセスのリソース使用量を表示する。"""

    def __init__(
            self,
            parent: QObject = None,
    ) -> None:
        """リソース使用量を表示するラベルを構築する。"""
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        """各リソース使用量を表示するラベルを配置する。"""
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

    def set_data(self, data: ResourceUsageGetResult) -> None:
        """リソース使用量を各表示ラベルへ反映する。"""
        self._l_cpu_percent.setText(f"CPU: {data.cpu_percent}%")
        self._l_memory.setText(f"RAM: {data.memory_mega_bytes:,} MB")
        self._l_disk_read_count.setText(f"Disk read: {data.disk_read_count:,}")
        self._l_disk_write_count.setText(f"Disk write: {data.disk_write_count:,}")
