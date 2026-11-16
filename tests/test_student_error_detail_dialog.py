from unittest.mock import Mock

import pytest

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
    table = StudentTableWidget()
    table.apply_loaded_rows([row])
    return table, student_id


def test_row_selection_emits_selected_student(qt_app) -> None:
    """セルの種類にかかわらず行選択として対応学生を通知する。"""
    from PyQt5.QtCore import QItemSelectionModel
    from autoprogen.control.widget_student_table import StudentTableColumns

    table, student_id = _create_table([
        StudentErrorCellDataTextEntry("検出しました", "詳細文"),
    ])
    emitted = []
    table.student_selection_changed.connect(
        lambda: emitted.append(table.selected_student_id())
    )
    index = table.model().index(0, StudentTableColumns.COL_ERROR)
    table.selectionModel().setCurrentIndex(
        index,
        QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows,
    )
    assert emitted == [student_id]
    table.close()


def test_table_uses_single_row_selection(qt_app) -> None:
    """学生テーブルが列単位や複数行ではなく単一行を選択する。"""
    from PyQt5.QtWidgets import QAbstractItemView

    table, _ = _create_table([])
    assert table.selectionBehavior() == QAbstractItemView.SelectRows
    assert table.selectionMode() == QAbstractItemView.SingleSelection
    table.close()


def test_detail_widget_displays_all_messages_read_only(qt_app) -> None:
    """詳細Widgetは複数エラーを編集不可のテキストで表示する。"""
    from autoprogen.control.widget_student_error_detail import StudentErrorDetailWidget

    widget = StudentErrorDetailWidget(
        error_entries=[
            StudentErrorCellDataTextEntry("最初のエラー", "最初のエラー\n詳細A"),
            StudentErrorCellDataTextEntry("次のエラー", "詳細B"),
        ],
    )
    displayed = widget._message_edit.toPlainText()
    assert "最初のエラー\n詳細A" in displayed
    assert "次のエラー\n詳細B" in displayed
    assert widget._message_edit.isReadOnly()
    widget.close()
