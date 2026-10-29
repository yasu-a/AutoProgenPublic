from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import get_ident
from unittest.mock import Mock

import pytest

from autoprogen.domain.model.value import StudentID
from autoprogen.service.student_change_event_bus import StudentChangeEventBus


@pytest.fixture
def qt_app(monkeypatch: pytest.MonkeyPatch):
    """画面を表示せずにQtイベントループを検証できるようにする。"""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PyQt5.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_worker_notifications_are_coalesced_on_gui_thread(qt_app) -> None:
    """別スレッドからの連続通知を学生ごとに一度だけGUIへ渡す。"""
    from autoprogen.control.qt_student_change_bridge import QtStudentChangeBridge
    from PyQt5.QtTest import QTest

    first_id = StudentID("21D5109047B")
    second_id = StudentID("26HG209871C")
    bus = StudentChangeEventBus()
    bridge = QtStudentChangeBridge(
        qt_app,
        student_ids=[first_id, second_id],
        student_change_event_bus=bus,
    )
    received: list[tuple[StudentID, int]] = []
    bridge.student_changed.connect(lambda student_id: received.append((student_id, get_ident())))

    def notify_from_worker() -> None:
        """学生変更をワーカースレッドから発行する。"""
        bus.notify(first_id)
        bus.notify(first_id)
        bus.notify(second_id)
        bus.notify(first_id)

    with ThreadPoolExecutor(max_workers=1) as executor:
        executor.submit(notify_from_worker).result()

    for _ in range(20):
        QTest.qWait(10)
        if len(received) == 2:
            break

    assert received == [(first_id, get_ident()), (second_id, get_ident())]
    bridge.stop()


def test_stop_discards_queued_notifications(qt_app) -> None:
    """終了時には購読と配送待ちの通知を破棄する。"""
    from autoprogen.control.qt_student_change_bridge import QtStudentChangeBridge

    student_id = StudentID("21D5109047B")
    bus = StudentChangeEventBus()
    bridge = QtStudentChangeBridge(
        qt_app,
        student_ids=[student_id],
        student_change_event_bus=bus,
    )
    received: list[StudentID] = []
    bridge.student_changed.connect(received.append)

    bus.notify(student_id)
    bridge.stop()
    bridge.stop()
    bus.notify(student_id)
    qt_app.processEvents()

    assert received == []


def test_student_table_replaces_only_the_notified_row(qt_app) -> None:
    """テーブルは通知された学生行だけを元の位置で置き換える。"""
    from autoprogen.control.widget_student_table import StudentTableWidget
    from PyQt5.QtTest import QTest

    first_id = StudentID("21D5109047B")
    second_id = StudentID("26HG209871C")
    bus = StudentChangeEventBus()
    row_loader = Mock()
    table = StudentTableWidget(
        student_change_event_bus=bus,
        student_table_load_usecase=row_loader,
    )
    from autoprogen.usecase.student_table_load import StudentTableRowSnapshot

    first_row = Mock(spec=StudentTableRowSnapshot, student_id=first_id)
    second_row = Mock(spec=StudentTableRowSnapshot, student_id=second_id)
    updated_second_row = Mock(spec=StudentTableRowSnapshot, student_id=second_id)
    row_loader.execute_row.return_value = updated_second_row
    table.apply_loaded_rows([first_row, second_row])
    changed_rows: list[int] = []
    table.model().dataChanged.connect(lambda start, _: changed_rows.append(start.row()))

    bus.notify(second_id)
    for _ in range(20):
        QTest.qWait(10)
        if changed_rows:
            break

    assert changed_rows == [1]
    row_loader.execute_row.assert_called_once_with(second_id)
    assert table.model()._student_ids == [first_id, second_id]
    assert table._model_data_provider._provider._row_snapshots[first_id] is first_row
    assert table._model_data_provider._provider._row_snapshots[second_id] is updated_second_row
    table.shutdown()
    bus.notify(first_id)
    qt_app.processEvents()
    assert changed_rows == [1]


def test_loaded_table_uses_snapshot_until_student_changes(qt_app) -> None:
    """全件ロード直後はDB取得を繰り返さず、変更行だけ再取得する。"""
    from PyQt5.QtCore import Qt
    from PyQt5.QtTest import QTest

    from autoprogen.control.widget_student_table import StudentTableWidget
    from autoprogen.domain.model.stage import BuildStage, CompileStage, ExecuteStage, TestStage
    from autoprogen.domain.model.student_mark import StudentMark
    from autoprogen.usecase.dto.student_table_cell_data import (
        StudentErrorCellData,
        StudentIDCellData,
        StudentNameCellData,
        StudentStageStateCellData,
    )
    from autoprogen.usecase.student_table_load import StudentTableRowSnapshot

    student_id = StudentID("21D5109047B")
    stage_cells = {
        stage_type: StudentStageStateCellData(student_id, stage_type, {})
        for stage_type in (BuildStage, CompileStage, ExecuteStage, TestStage)
    }
    row = StudentTableRowSnapshot(
        student_id=student_id,
        id_cell=StudentIDCellData(student_id, str(student_id), True),
        name_cell=StudentNameCellData(student_id, "ロード済みの名前"),
        stage_cells=stage_cells,
        error_cell=StudentErrorCellData(student_id, []),
        mark=StudentMark(student_id=student_id, score=50),
    )
    row_loader = Mock()
    bus = StudentChangeEventBus()
    table = StudentTableWidget(
        student_change_event_bus=bus,
        student_table_load_usecase=row_loader,
    )
    table.apply_loaded_rows([row])

    for column in range(table.model().columnCount()):
        table.model().data(table.model().index(0, column), Qt.DisplayRole)
    table.model().data(table.model().index(0, 0), Qt.FontRole)
    table.model().data(table.model().index(0, 0), Qt.ForegroundRole)
    table.model().data(table.model().index(0, 7), Qt.ToolTipRole)

    row_loader.execute_row.assert_not_called()

    row_loader.execute_row.return_value = replace(
        row, name_cell=StudentNameCellData(student_id, "更新後の名前")
    )
    changed_rows: list[int] = []
    table.model().dataChanged.connect(lambda start, _: changed_rows.append(start.row()))
    bus.notify(student_id)
    for _ in range(20):
        QTest.qWait(10)
        if changed_rows:
            break

    assert changed_rows == [0]
    assert table.model().data(table.model().index(0, 1), Qt.DisplayRole) == "更新後の名前"
    row_loader.execute_row.assert_called_once_with(student_id)
    table.shutdown()
