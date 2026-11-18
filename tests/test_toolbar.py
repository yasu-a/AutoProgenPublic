from unittest.mock import Mock

import pytest
from PyQt5.QtWidgets import QApplication

from autoprogen.control.widget_toolbar import ToolBar


@pytest.fixture
def qt_app(monkeypatch: pytest.MonkeyPatch) -> QApplication:
    """画面を表示せずに利用できるQApplicationを返す。"""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_toolbar_labels_bulk_grading_action(
        qt_app: QApplication,
) -> None:
    """一括採点ボタンの対象範囲を誤解しない名称を表示する。"""
    toolbar = ToolBar(task_manager=Mock())

    assert toolbar._a_mark.text() == "一括採点"
