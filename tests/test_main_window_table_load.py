from unittest.mock import Mock

import pytest


def test_main_window_loads_table_with_progress_dialog(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """メインウィンドウ起動直後に進捗ダイアログ経由で全件ロードする。"""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PyQt5.QtTest import QTest
    from PyQt5.QtWidgets import QApplication

    from autoprogen.control.dialog_progress import AbstractProgressDialog
    from autoprogen.control.window_main import MainWindow

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    rows = [Mock()]
    progress_dialog = Mock(return_value=rows)
    monkeypatch.setattr(AbstractProgressDialog, "run_blocking_task", progress_dialog)

    def init_ui(window: MainWindow) -> None:
        """画面配置を省き、ロード処理への接続だけを検証する。"""
        window._w_student_table = Mock()

    def init_signals(_: MainWindow) -> None:
        """画面全体のシグナル接続を省略する。"""

    monkeypatch.setattr(MainWindow, "_init_ui", init_ui)
    monkeypatch.setattr(MainWindow, "_init_signals", init_signals)
    project_container = Mock()
    window = MainWindow(
        navigator=Mock(),
        app_container=Mock(),
        project_container=project_container,
    )
    window.show()
    QTest.qWait(30)

    progress_dialog.assert_called_once_with(
        parent=window,
        title="学生テーブルの読み込み",
        initial_message="学生の表示データを読み込み中...",
        task_func=project_container.student_table_load_usecase.execute,
    )
    window._w_student_table.apply_loaded_rows.assert_called_once_with(rows)
    window.hide()
