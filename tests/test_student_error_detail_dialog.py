from unittest.mock import Mock

import pytest

from autoprogen.domain.model.stage import BuildStage, CompileStage, ExecuteStage, TestStage
from autoprogen.domain.model.student_mark import StudentMark
from autoprogen.domain.model.value import StudentID
from autoprogen.service.student_change_event_bus import StudentChangeEventBus
from autoprogen.usecase.dto.student_table_cell_data import (
    StudentErrorCellData,
    StudentErrorCellDataTextEntry,
    StudentIDCellData,
    StudentNameCellData,
    StudentStageStateCellData,
)
from autoprogen.usecase.student_table_load import StudentTableRowSnapshot


@pytest.fixture
def qt_app(monkeypatch: pytest.MonkeyPatch):
    """ディスプレイを使わずQtウィジェットを検証する。"""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PyQt5.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _create_table(entries: list[StudentErrorCellDataTextEntry]):
    """エラー内容を持つ学生を1行だけ表示した表を作る。"""
    from autoprogen.control.widget_student_table import StudentTableWidget

    student_id = StudentID("21D5109047B")
    row = StudentTableRowSnapshot(
        student_id=student_id,
        id_cell=StudentIDCellData(student_id, str(student_id), True),
        name_cell=StudentNameCellData(student_id, "試験 太郎"),
        stage_cells={
            stage_type: StudentStageStateCellData(student_id, stage_type, {})
            for stage_type in (BuildStage, CompileStage, ExecuteStage, TestStage)
        },
        error_cell=StudentErrorCellData(student_id, entries),
        mark=StudentMark(student_id=student_id, score=None),
    )
    table = StudentTableWidget(
        student_change_event_bus=StudentChangeEventBus(),
        student_table_load_usecase=Mock(),
    )
    table.apply_loaded_rows([row])
    return table, student_id


def test_error_column_click_emits_student_id(qt_app) -> None:
    """エラーがあるセルを押すと対応学生の通知を送る。"""
    from PyQt5.QtCore import QItemSelectionModel
    from autoprogen.control.widget_student_table import StudentTableColumns

    table, student_id = _create_table([
        StudentErrorCellDataTextEntry("検出しました", "詳細文"),
    ])
    emitted = []
    table.error_cell_triggered.connect(emitted.append)
    index = table.model().index(0, StudentTableColumns.COL_ERROR)
    table.setCurrentIndex(index)
    table.selectionModel().select(index, QItemSelectionModel.ClearAndSelect)
    table._on_cell_triggered()
    assert emitted == [student_id]
    table.shutdown()
    table.close()


def test_empty_error_column_does_not_open_dialog(qt_app) -> None:
    """エラーのないセルを押しても通知しない。"""
    from PyQt5.QtCore import QItemSelectionModel
    from autoprogen.control.widget_student_table import StudentTableColumns

    table, _ = _create_table([])
    emitted = []
    table.error_cell_triggered.connect(emitted.append)
    index = table.model().index(0, StudentTableColumns.COL_ERROR)
    table.setCurrentIndex(index)
    table.selectionModel().select(index, QItemSelectionModel.ClearAndSelect)
    table._on_cell_triggered()
    assert emitted == []
    table.shutdown()
    table.close()


def test_dialog_displays_all_messages_read_only(qt_app) -> None:
    """ダイアログは複数エラーの詳細を編集不可のテキストで表示する。"""
    from autoprogen.control.dialog_student_error_detail import StudentErrorDetailDialog

    dialog = StudentErrorDetailDialog(
        student_id=StudentID("21D5109047B"),
        error_entries=[
            StudentErrorCellDataTextEntry("最初のエラー", "最初のエラー\n詳細A"),
            StudentErrorCellDataTextEntry("次のエラー", "詳細B"),
        ],
    )
    displayed = dialog._message_edit.toPlainText()
    assert "最初のエラー\n詳細A" in displayed
    assert "次のエラー\n詳細B" in displayed
    assert dialog._message_edit.isReadOnly()
    dialog.close()
