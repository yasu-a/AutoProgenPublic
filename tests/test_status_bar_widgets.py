from unittest.mock import Mock

import pytest
from PyQt5.QtWidgets import QApplication

from autoprogen.control.widget_status_process_resource_usage import (
    ProcessResourceUsageStatusBarWidget,
)
from autoprogen.control.widget_status_unstable_version_notif import (
    UnstableVersionNotificationStatusBarWidget,
)
from autoprogen.control.window_main import MainWindow
from autoprogen.usecase.dto.resource_usage import ResourceUsageGetResult


@pytest.fixture
def qt_app(monkeypatch: pytest.MonkeyPatch) -> QApplication:
    """画面を表示せずに利用できるQApplicationを返す。"""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_resource_usage_widget_presents_set_data(qt_app: QApplication) -> None:
    """Widgetは渡されたリソース使用量だけを表示形式へ変換する。"""
    widget = ProcessResourceUsageStatusBarWidget()

    widget.set_data(ResourceUsageGetResult(
        disk_read_count=1234,
        disk_write_count=5678,
        cpu_percent=12,
        memory_mega_bytes=345,
    ))

    assert widget._l_disk_read_count.text() == "Disk read: 1,234"
    assert widget._l_disk_write_count.text() == "Disk write: 5,678"
    assert widget._l_cpu_percent.text() == "CPU: 12%"
    assert widget._l_memory.text() == "RAM: 345 MB"


def test_unstable_version_widget_presents_stability(qt_app: QApplication) -> None:
    """Widgetは渡された安定性だけに応じて警告の表示を切り替える。"""
    widget = UnstableVersionNotificationStatusBarWidget()

    widget.set_data(False)
    assert not widget.isHidden()

    widget.set_data(True)
    assert widget.isHidden()


def test_main_window_updates_resource_usage_view(qt_app: QApplication) -> None:
    """MainWindowがFacadeの取得結果をリソース表示へ渡す。"""
    window = Mock()
    data = ResourceUsageGetResult(1, 2, 3, 4)
    window._facade.get_resource_usage.return_value = data

    MainWindow._MainWindow__update_resource_usage(window)

    window._sb_process_resource_usage.set_data.assert_called_once_with(data)
