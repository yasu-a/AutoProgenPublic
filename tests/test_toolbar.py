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
    toolbar = ToolBar()

    assert toolbar._a_mark.text() == "一括採点"


def test_toolbar_buttons_follow_main_window_state(qt_app: QApplication) -> None:
    """外部からのbusy更新で各操作が切り替わり、中断は使える。"""
    toolbar = ToolBar()
    toolbar.update_button_state(is_task_alive=False)
    assert toolbar._a_run.isEnabled()
    assert toolbar._a_mark.isEnabled()
    assert not toolbar._a_stop.isEnabled()

    toolbar.update_button_state(is_task_alive=True)
    for action in (
        toolbar._a_run,
        toolbar._a_delete,
        toolbar._a_settings,
        toolbar._a_project_settings,
        toolbar._a_edit_testcases,
        toolbar._a_mark,
        toolbar._a_export_scores,
    ):
        assert not action.isEnabled()
    assert toolbar._a_stop.isEnabled()
    assert toolbar._a_about.isEnabled()

    toolbar.update_button_state(is_task_alive=False)
    assert toolbar._a_run.isEnabled()
    assert toolbar._a_mark.isEnabled()
    assert not toolbar._a_stop.isEnabled()
    assert not hasattr(toolbar, "_task_manager")
    assert not hasattr(toolbar, "_ToolBar__state_update_timer")
    toolbar.close()
