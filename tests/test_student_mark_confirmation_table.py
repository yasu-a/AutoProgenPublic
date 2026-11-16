"""学生テーブルの採点確定チェック操作を検証する。"""

from unittest.mock import Mock

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QStyle, QStyleOptionViewItem

from autoprogen.control.widget_student_table import (
    StudentTableColumns,
    StudentTableWidget,
)
from autoprogen.control.widget_toolbar import ToolBar
from autoprogen.control.window_main import MainWindow
from autoprogen.domain.model.stage import BuildStage, CompileStage, ExecuteStage, TestStage
from autoprogen.domain.model.student_mark import StudentMark
from autoprogen.domain.model.value import StudentID
from autoprogen.usecase.dto.student_table_cell_data import (
    StudentErrorCellData,
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
        mark: StudentMark,
        *,
        has_submission: bool = True,
) -> StudentTableRowSnapshot:
    """指定した採点状態を持つ学生テーブルの一行を返す。"""
    student_id = mark.student_id
    return StudentTableRowSnapshot(
        student_id=student_id,
        id_cell=StudentIDCellData(student_id, str(student_id), has_submission),
        name_cell=StudentNameCellData(student_id, "試験 太郎"),
        stage_cells={
            stage_type: StudentStageStateCellData(student_id, stage_type, {})
            for stage_type in (BuildStage, CompileStage, ExecuteStage, TestStage)
        },
        error_cell=StudentErrorCellData(student_id, []),
        mark=mark,
    )


def _table(mark: StudentMark) -> StudentTableWidget:
    """指定した採点状態を一行だけ表示する学生テーブルを返す。"""
    table = StudentTableWidget()
    table.resize(1000, 200)
    table.apply_loaded_rows([_row(mark)])
    table.show()
    QApplication.processEvents()
    return table


def test_mark_cell_check_state_and_operability(qt_app: QApplication) -> None:
    """確定状態を表示し、点数がある学生だけをチェック操作可能にする。"""
    student_id = StudentID("21D5109047B")
    table = _table(StudentMark(student_id, 80, confirmed=False))
    index = table.model().index(0, StudentTableColumns.COL_SCORE)

    assert table.model().data(index, Qt.CheckStateRole) == Qt.Unchecked
    assert table.model().flags(index) & Qt.ItemIsUserCheckable

    table.apply_loaded_rows([_row(StudentMark(student_id, None))])
    index = table.model().index(0, StudentTableColumns.COL_SCORE)
    assert table.model().data(index, Qt.CheckStateRole) == Qt.Unchecked
    assert not table.model().flags(index) & Qt.ItemIsUserCheckable


def test_unsubmitted_student_id_remains_red(qt_app: QApplication) -> None:
    """未提出の学生だけは従来どおり学籍番号を赤色で表示する。"""
    student_id = StudentID("21D5109047B")
    table = _table(StudentMark(student_id, None))
    table.apply_loaded_rows([
        _row(StudentMark(student_id, None), has_submission=False),
    ])
    index = table.model().index(0, StudentTableColumns.COL_STUDENT_ID)
    table.selectRow(0)
    foreground = table.model().data(index, Qt.ForegroundRole)
    assert foreground.name() == QColor("red").name()
    assert not table.selected_student_has_submission()

    table.apply_loaded_rows([
        _row(StudentMark(student_id, None), has_submission=True),
    ])
    index = table.model().index(0, StudentTableColumns.COL_STUDENT_ID)
    table.selectRow(0)
    assert table.model().data(index, Qt.ForegroundRole) is None
    assert table.selected_student_has_submission()


def test_check_click_changes_confirmation_and_score_click_selects_row(
        qt_app: QApplication,
) -> None:
    """チェック操作を維持し、点数文字列のクリックは行選択だけを行う。"""
    student_id = StudentID("21D5109047B")
    table = _table(StudentMark(student_id, 80, confirmed=True))
    confirmation_requests: list[tuple[StudentID, bool]] = []
    table.mark_confirmation_change_requested.connect(
        lambda target, confirmed: confirmation_requests.append((target, confirmed)),
    )

    index = table.model().index(0, StudentTableColumns.COL_SCORE)
    option = QStyleOptionViewItem()
    table.itemDelegate(index).initStyleOption(option, index)
    option.rect = table.visualRect(index)
    indicator_rect = table.style().subElementRect(
        QStyle.SE_ItemViewItemCheckIndicator,
        option,
        table,
    )
    QTest.mouseClick(
        table.viewport(),
        Qt.LeftButton,
        pos=indicator_rect.center(),
    )

    assert confirmation_requests == [(student_id, False)]
    assert table.selected_student_id() == student_id

    score_position = table.visualRect(index).center()
    assert not indicator_rect.contains(score_position)
    QTest.mouseClick(table.viewport(), Qt.LeftButton, pos=score_position)

    assert confirmation_requests == [(student_id, False)]
    assert table.selected_student_id() == student_id


def test_confirmation_request_preserves_score_and_saves(
        qt_app: QApplication,
) -> None:
    """メイン画面は点数を維持して確定状態だけを保存する。"""
    student_id = StudentID("21D5109047B")
    student_mark = StudentMark(student_id, 80, confirmed=True)
    window = Mock()
    MainWindow._MainWindow__w_student_table_mark_confirmation_change_requested(
        window,
        student_id,
        False,
    )

    window._facade.set_student_mark_confirmation.assert_called_once_with(
        student_id,
        False,
    )


def test_toolbar_labels_bulk_action_as_unconfirmed_grading(
        qt_app: QApplication,
) -> None:
    """一括採点ボタンが未確定学生だけを対象とすることを明示する。"""
    toolbar = ToolBar(task_manager=Mock())

    assert toolbar._a_mark.text() == "未確定を採点"
