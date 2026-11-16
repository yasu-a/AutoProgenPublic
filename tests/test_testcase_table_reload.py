from unittest.mock import Mock

import pytest

from autoprogen.domain.model.testcase_config import TestCaseConfig as CaseConfig
from autoprogen.domain.model.value import TestCaseID as CaseID
from autoprogen.usecase.dto.testcase_list_edit import (
    TestCaseListEditTestCaseSummary as CaseSummary,
)


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
    """一覧の変更を保存した場合だけ変更済みとして扱う。"""
    from autoprogen.control.dialog_testcase_list_edit import TestCaseListEditDialog

    summary_usecase = Mock()
    summary_usecase.execute.return_value = []
    put_usecase = Mock()
    dialog = TestCaseListEditDialog(
        global_settings_get_usecase=Mock(),
        test_test_stage_usecase=Mock(),
        testcase_list_summary_usecase=summary_usecase,
        testcase_delete_usecase=Mock(),
        testcase_get_usecase=Mock(),
        testcase_put_usecase=put_usecase,
    )

    assert not dialog.has_changes
    config = CaseConfig.create_default(CaseID("case-a"))
    dialog._w_testcase_edit.set_data([config])
    assert dialog.has_unsaved_changes()
    dialog._save()
    assert dialog.has_changes
    put_usecase.execute.assert_called_once_with(config)


def test_testcase_dialog_sets_and_gets_list_data(qt_app) -> None:
    """テストケース一覧を外部から設定し、同じ概要を取得できる。"""
    from autoprogen.control.dialog_testcase_list_edit import TestCaseListEditDialog

    summaries = [
        CaseSummary(
            testcase_id=CaseID("case-a"),
            name="case-a",
            has_stdin=True,
            num_normal_files=2,
        ),
    ]
    initial = [CaseConfig.create_default(CaseID("case-a"))]
    summary_usecase = Mock()
    summary_usecase.execute.return_value = summaries
    get_usecase = Mock()
    get_usecase.execute.return_value = initial[0]
    dialog = TestCaseListEditDialog(
        global_settings_get_usecase=Mock(),
        test_test_stage_usecase=Mock(),
        testcase_list_summary_usecase=summary_usecase,
        testcase_delete_usecase=Mock(),
        testcase_get_usecase=get_usecase,
        testcase_put_usecase=Mock(),
    )

    assert dialog.get_data() == initial
    assert dialog._w_testcase_edit._w_testcase_list.count() == 1

    dialog.set_data([])

    assert dialog.get_data() == []
    assert dialog._w_testcase_edit._w_testcase_list.count() == 0
    dialog.set_data(initial)
    dialog.reject()


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
        main_window_facade=Mock(),
    )
    window.load_student_table = Mock()

    window._MainWindow__tool_bar_triggered("edit-testcases")

    navigator.open_testcase_list_edit_dialog.assert_called_once_with(window)
    assert window.load_student_table.call_count == int(has_changes)
