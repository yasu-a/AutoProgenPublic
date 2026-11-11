from time import perf_counter

import pytest


def test_initialized_table_stays_idle_and_reflects_mark_change(
        initialized_project_from_archive,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """初期表示後はDBへ接続せず、採点変更時だけ対象行を速やかに再読み込みする。"""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from PyQt5.QtCore import Qt
    from PyQt5.QtTest import QTest
    from PyQt5.QtWidgets import QApplication

    from autoprogen.control.widget_student_table import (
        StudentTableColumns,
        StudentTableWidget,
    )
    from autoprogen.domain.model.student_mark import StudentMark

    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    project_container = initialized_project_from_archive(
        archive_name="grading_smoke",
        project_name="student_table_idle_test",
    )
    database_io = project_container.project_database_io
    original_create_connection = database_io._create_connection
    connection_count = 0

    def count_database_connection():
        """実DB接続を生成するたびに計測値を増やす。"""
        nonlocal connection_count
        connection_count += 1
        return original_create_connection()

    monkeypatch.setattr(database_io, "_create_connection", count_database_connection)
    table = StudentTableWidget(
        student_change_event_bus=project_container.student_change_event_bus,
        student_table_load_usecase=project_container.student_table_load_usecase,
    )

    try:
        rows = project_container.student_table_load_usecase.execute(
            progress_callback=lambda _: None,
        )
        table.apply_loaded_rows(rows)
        assert rows

        # 初回ロード後に放置しても、旧20msポーリングのようなDB接続を発生させない。
        connection_count = 0
        QTest.qWait(250)
        assert connection_count == 0

        student_id = rows[0].student_id
        new_score = 98 if rows[0].mark.is_marked and rows[0].mark.score == 99 else 99
        changed_rows: list[int] = []
        table.model().dataChanged.connect(
            lambda start, _: changed_rows.append(start.row()),
        )

        # 変更通知から対象行の表示反映までを、利用者が待たされない時間内で確認する。
        started_at = perf_counter()
        project_container.student_mark_put_usecase.execute(
            StudentMark(student_id=student_id, score=new_score),
        )
        while not changed_rows and perf_counter() - started_at < 0.5:
            QTest.qWait(10)
        elapsed = perf_counter() - started_at

        row_index = table.model().get_row_of_student(student_id)
        score_index = table.model().index(row_index, StudentTableColumns.COL_SCORE)
        assert changed_rows == [row_index]
        assert table.model().data(score_index, Qt.DisplayRole) == str(new_score)
        assert elapsed < 0.5
    finally:
        table.shutdown()

