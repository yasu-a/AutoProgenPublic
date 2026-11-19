from dataclasses import replace
from unittest.mock import Mock

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QLabel, QMessageBox, QDockWidget

from autoprogen.control.widget_student_table import (
    StudentTableColumns,
    StudentTableWidget,
)
from autoprogen.control.window_main import MainWindow
from autoprogen.domain.model.stage import BuildStage, CompileStage, ExecuteStage, TestStage
from autoprogen.domain.model.student_mark import StudentMark
from autoprogen.domain.model.value import StudentID
from autoprogen.usecase.dto.student_table_cell_data import (
    StudentErrorCellData,
    StudentErrorCellDataTextEntry,
    StudentIDCellData,
    StudentNameCellData,
    StudentStageStateCellData,
)
from autoprogen.usecase.main_window import StudentTableRowSnapshot


TestStage.__test__ = False


@pytest.fixture
def qt_app(monkeypatch: pytest.MonkeyPatch) -> QApplication:
    """画面を表示せずに利用できるQApplicationを返す。"""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _row(
        student_id: StudentID,
        *,
        has_submission: bool,
        has_error: bool,
        score: int | None,
) -> StudentTableRowSnapshot:
    """セルの操作可否を指定した学生テーブルの一行を返す。"""
    entries = []
    if has_error:
        entries.append(StudentErrorCellDataTextEntry("検出しました", "詳細文"))
    return StudentTableRowSnapshot(
        student_id=student_id,
        id_cell=StudentIDCellData(student_id, str(student_id), has_submission),
        name_cell=StudentNameCellData(student_id, "試験 太郎"),
        stage_cells={
            stage_type: StudentStageStateCellData(student_id, stage_type, {})
            for stage_type in (BuildStage, CompileStage, ExecuteStage, TestStage)
        },
        error_cell=StudentErrorCellData(student_id, entries),
        mark=StudentMark(
            student_id,
            score,
        ),
    )


def _table() -> tuple[StudentTableWidget, StudentID, StudentID]:
    """操作可能条件が異なる二人を表示した学生テーブルを返す。"""
    first = StudentID("21D5109047B")
    second = StudentID("24A0007521M")
    table = StudentTableWidget()
    table.resize(1200, 240)
    table.apply_loaded_rows([
        _row(first, has_submission=True, has_error=True, score=80),
        _row(second, has_submission=False, has_error=False, score=None),
    ])
    table.show()
    QApplication.processEvents()
    return table, first, second


def _click(table: StudentTableWidget, row: int, column: int) -> None:
    """指定セルの中央をマウスでクリックする。"""
    index = table.model().index(row, column)
    QTest.mouseClick(
        table.viewport(),
        Qt.LeftButton,
        pos=table.visualRect(index).center(),
    )


def test_direct_cell_clicks_emit_only_available_student_actions(
        qt_app: QApplication,
) -> None:
    """クリックされたセルと学生に対応する利用可能な操作だけを通知する。"""
    table, first, second = _table()
    folder_requests: list[StudentID] = []
    scoring_requests: list[StudentID] = []
    error_requests: list[StudentID] = []
    table.student_id_cell_triggered.connect(folder_requests.append)
    table.mark_result_cell_triggered.connect(scoring_requests.append)
    table.error_cell_triggered.connect(error_requests.append)

    _click(table, 0, StudentTableColumns.COL_STUDENT_ID)
    _click(table, 1, StudentTableColumns.COL_STUDENT_ID)
    _click(table, 0, StudentTableColumns.COL_SCORE)
    _click(table, 1, StudentTableColumns.COL_SCORE)
    _click(table, 0, StudentTableColumns.COL_ERROR)
    _click(table, 1, StudentTableColumns.COL_ERROR)
    _click(table, 0, StudentTableColumns.COL_NAME)
    _click(table, 0, StudentTableColumns.COL_STAGE_BUILD)

    assert folder_requests == [first]
    assert scoring_requests == [first, second]
    assert error_requests == [first]
    table.close()


def test_actionable_cells_use_link_style_and_pointing_cursor(
        qt_app: QApplication,
) -> None:
    """操作可能なセルだけをリンク風表示とポインタカーソルにする。"""
    table, _, _ = _table()
    model = table.model()
    live_id = model.index(0, StudentTableColumns.COL_STUDENT_ID)
    dead_id = model.index(1, StudentTableColumns.COL_STUDENT_ID)
    score = model.index(1, StudentTableColumns.COL_SCORE)
    error = model.index(0, StudentTableColumns.COL_ERROR)
    empty_error = model.index(1, StudentTableColumns.COL_ERROR)

    for index in (live_id, score, error):
        assert model.data(index, Qt.FontRole).underline()
        assert model.data(index, Qt.ForegroundRole) == QColor("blue")
        QTest.mouseMove(table.viewport(), table.visualRect(index).center())
        assert table.viewport().cursor().shape() == Qt.PointingHandCursor

    assert not model.data(dead_id, Qt.FontRole).underline()
    assert model.data(dead_id, Qt.ForegroundRole) == QColor("red").darker()
    assert model.data(empty_error, Qt.FontRole) is None
    assert model.data(empty_error, Qt.ForegroundRole) is None
    QTest.mouseMove(table.viewport(), table.visualRect(empty_error).center())
    assert table.viewport().cursor().shape() != Qt.PointingHandCursor

    assert model.data(score, Qt.CheckStateRole) is None
    assert not model.flags(score) & Qt.ItemIsUserCheckable
    table.close()


def test_row_update_refreshes_error_link_style(qt_app: QApplication) -> None:
    """対象行の差分更新後にエラーセルのリンク状態を更新する。"""
    table, first, _ = _table()
    error = table.model().index(0, StudentTableColumns.COL_ERROR)
    assert table.model().data(error, Qt.FontRole).underline()

    table.replace_loaded_row(
        _row(first, has_submission=True, has_error=False, score=80),
    )

    assert table.model().data(error, Qt.DisplayRole) == ""
    assert table.model().data(error, Qt.FontRole) is None
    assert table.model().data(error, Qt.ForegroundRole) is None
    table.close()


def test_main_window_routes_direct_cell_actions_to_existing_boundaries(
        qt_app: QApplication,
) -> None:
    """メイン画面はセル操作をFacade・Navigator・Dockへ接続する。"""
    student_id = StudentID("21D5109047B")
    window = Mock()
    window._task_manager.is_empty.return_value = True
    window._MainWindow__show_student_error_detail = Mock()

    MainWindow._MainWindow__w_student_table_student_id_cell_triggered(
        window,
        student_id,
    )
    MainWindow._MainWindow__w_student_table_mark_result_cell_triggered(
        window,
        student_id,
    )
    MainWindow._MainWindow__w_student_table_error_cell_triggered(
        window,
        student_id,
    )

    window._facade.open_student_submission_folder.assert_called_once_with(student_id)
    window._navigator.open_scoring_dialog_for_student.assert_called_once_with(
        window,
        student_id,
    )
    window._MainWindow__show_student_error_detail.assert_called_once_with(student_id)


def test_scoring_cell_keeps_existing_task_guard(
        qt_app: QApplication,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """実行中は点数セルから個別採点を開始せず警告する。"""
    student_id = StudentID("21D5109047B")
    window = Mock()
    window._task_manager.is_empty.return_value = False
    warning = Mock()
    monkeypatch.setattr(QMessageBox, "warning", warning)

    MainWindow._MainWindow__w_student_table_mark_result_cell_triggered(
        window,
        student_id,
    )

    window._navigator.open_scoring_dialog_for_student.assert_not_called()
    warning.assert_called_once()


def test_main_window_busy_state_locks_table_and_hides_dock(
        qt_app: QApplication,
) -> None:
    """実行中は表の操作を禁止してDockを隠し、終了後も自動再表示しない。"""
    window = Mock()
    window._student_error_dock = QDockWidget()
    previous = QLabel("古いエラー詳細")
    window._student_error_dock.setWidget(previous)
    window._student_error_dock.show()
    window._task_manager.is_empty.return_value = False

    MainWindow._on_task_busy_changed(window, True)

    window._tool_bar.update_button_state.assert_called_with(is_task_alive=True)
    window._w_student_table.set_interaction_enabled.assert_called_with(False)
    assert not window._student_error_dock.isEnabled()
    assert window._student_error_dock.isHidden()

    window._task_manager.is_empty.return_value = True
    MainWindow._on_task_busy_changed(window, False)
    window._tool_bar.update_button_state.assert_called_with(is_task_alive=False)
    window._w_student_table.set_interaction_enabled.assert_called_with(True)
    assert window._student_error_dock.isEnabled()
    assert window._student_error_dock.isHidden()
    window._student_error_dock.close()


def test_main_window_ignores_stale_busy_signal(qt_app: QApplication) -> None:
    """遅延した通知よりTaskManagerの現在の状態を優先する。"""
    window = Mock()
    window._student_error_dock = QDockWidget()
    window._task_manager.is_empty.return_value = False
    MainWindow._on_task_busy_changed(window, False)
    window._tool_bar.update_button_state.assert_called_once_with(is_task_alive=True)
    window._student_error_dock.close()


def test_main_window_rejects_programmatic_cell_actions_when_busy(
        qt_app: QApplication,
) -> None:
    """無効な表のシグナルが外部から届いてもDockやフォルダを開かない。"""
    student_id = StudentID("21D5109047B")
    window = Mock()
    window._task_manager.is_empty.return_value = False
    MainWindow._MainWindow__w_student_table_student_id_cell_triggered(
        window, student_id,
    )
    MainWindow._MainWindow__w_student_table_error_cell_triggered(
        window, student_id,
    )
    MainWindow._MainWindow__show_student_error_detail(window, student_id)
    window._facade.open_student_submission_folder.assert_not_called()
    window._MainWindow__show_student_error_detail.assert_not_called()
    window._student_error_detail_coordinator.create_widget.assert_not_called()


def test_about_action_does_not_force_busy_state(qt_app: QApplication) -> None:
    """Aboutを開いただけでツールバーの実行中状態に切り替えない。"""
    window = Mock()
    MainWindow._MainWindow__tool_bar_triggered(window, "about")
    window._navigator.open_about_dialog.assert_called_once_with(window)
    window._tool_bar.update_button_state.assert_not_called()


def test_error_cell_replaces_detail_dock_for_clicked_student(
        qt_app: QApplication,
) -> None:
    """別学生のエラーを押すと下部Dockの内容とタイトルを差し替える。"""
    first = StudentID("21D5109047B")
    second = StudentID("24A0007521M")
    window = Mock()
    window._student_error_dock = QDockWidget()
    window._facade.get_student_name.side_effect = (
        "試験 太郎",
        "試験 花子",
    )
    first_widget = QLabel("最初の詳細")
    second_widget = QLabel("次の詳細")
    window._student_error_detail_coordinator.create_widget.side_effect = (
        first_widget,
        second_widget,
    )

    MainWindow._MainWindow__show_student_error_detail(window, first)
    assert window._student_error_dock.widget() is first_widget
    assert window._student_error_dock.windowTitle() == (
        f"エラーの詳細 - {first} 試験 太郎"
    )

    MainWindow._MainWindow__show_student_error_detail(window, second)
    assert window._student_error_dock.widget() is second_widget
    assert window._student_error_dock.windowTitle() == (
        f"エラーの詳細 - {second} 試験 花子"
    )
    assert window._student_error_dock.isVisible()
    window._student_error_dock.close()


def test_excluded_row_background_updates_with_snapshot(
        qt_app: QApplication,
) -> None:
    """除外指定の追加・解除に伴い、全列の背景色キャッシュが更新される。"""
    table, student_id, _ = _table()
    model = table.model()
    original_colors = [
        model.data(model.index(0, column), Qt.BackgroundRole)
        for column in range(model.columnCount())
    ]
    row = _row(student_id, has_submission=True, has_error=True, score=80)
    table.replace_loaded_row(replace(row, bulk_grading_skipped=True))

    for column in range(model.columnCount()):
        assert model.data(model.index(0, column), Qt.BackgroundRole) == QColor("#e6e6e6")

    table.replace_loaded_row(row)
    assert [
        model.data(model.index(0, column), Qt.BackgroundRole)
        for column in range(model.columnCount())
    ] == original_colors
    table.close()
