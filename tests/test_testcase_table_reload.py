from unittest.mock import Mock

import pytest


@pytest.fixture
def qt_app(monkeypatch: pytest.MonkeyPatch):
    """テストケース編集画面を表示せずに検証できるQt環境を返す。"""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PyQt5.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_testcase_dialog_tracks_modifications(qt_app) -> None:
    """編集通知がなければ未変更とし、通知後は閉じるまで変更状態を保持する。"""
    from autoprogen.control.dialog_testcase_list_edit import TestCaseListEditDialog

    summary_usecase = Mock()
    summary_usecase.execute.return_value = []
    dialog = TestCaseListEditDialog(
        global_settings_get_usecase=Mock(),
        test_test_stage_usecase=Mock(),
        testcase_list_summary_usecase=summary_usecase,
        testcase_create_new_name_usecase=Mock(),
        testcase_create_usecase=Mock(),
        testcase_copy_usecase=Mock(),
        testcase_delete_usecase=Mock(),
        testcase_get_usecase=Mock(),
        testcase_put_usecase=Mock(),
    )

    assert not dialog.has_changes
    dialog._w_testcase_edit.testcase_modified.emit()
    assert dialog.has_changes
    dialog.close()


@pytest.mark.parametrize("has_changes", [False, True])
def test_main_window_reloads_table_only_after_testcase_changes(
        qt_app,
        monkeypatch: pytest.MonkeyPatch,
        has_changes: bool,
) -> None:
    """テストケース編集画面を閉じた後、変更があった場合だけ全件ロードする。"""
    from autoprogen.control.window_main import MainWindow

    def init_ui(window: MainWindow) -> None:
        """ツールバーの操作に必要な最小限の状態を用意する。"""
        window._tool_bar = Mock()

    def init_signals(_: MainWindow) -> None:
        """このテストでは他の画面シグナルを接続しない。"""

    monkeypatch.setattr(MainWindow, "_init_ui", init_ui)
    monkeypatch.setattr(MainWindow, "_init_signals", init_signals)
    navigator = Mock()
    navigator.open_testcase_list_edit_dialog.return_value = has_changes
    window = MainWindow(
        navigator=navigator,
        app_container=Mock(),
        project_container=Mock(),
    )
    window.load_student_table = Mock()

    window._MainWindow__tool_bar_triggered("edit-testcases")

    navigator.open_testcase_list_edit_dialog.assert_called_once_with(window)
    assert window.load_student_table.call_count == int(has_changes)
