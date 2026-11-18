"""Excel出力直前の採点済みチェックを検証する。"""

from pathlib import Path
from unittest.mock import Mock

import pytest
from PyQt5.QtWidgets import QApplication, QMessageBox

from autoprogen.control.dialog_score_export import ScoreExportDialog
from autoprogen.domain.model.student_mark import StudentMark
from autoprogen.domain.model.value import StudentID, TargetID


@pytest.fixture
def qt_app(monkeypatch: pytest.MonkeyPatch) -> QApplication:
    """画面なしでQtを初期化する。"""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _dialog(tmp_path: Path, marks: list[StudentMark]):
    """実際のExcel書き込みを行わない採点出力画面を構築する。"""
    first = StudentID("21D5109047B")
    second = StudentID("24A0007521M")
    ids = [first, second]
    list_ids = Mock()
    list_ids.execute.return_value = ids
    list_marks = Mock()
    list_marks.execute.return_value = marks
    has_data = Mock()
    has_data.execute.return_value = False
    apply = Mock()
    apply.execute.return_value = None
    global_settings = Mock()
    global_settings.execute.return_value.backup_before_export = True
    list_worksheet_stats = Mock()
    list_worksheet_stats.execute.return_value = []
    dialog = ScoreExportDialog(
        global_settings_get_usecase=global_settings,
        score_excel_list_worksheet_stats_usecase=list_worksheet_stats,
        score_excel_has_data_usecase=has_data,
        score_excel_apply_usecase=apply,
        student_list_id_usecase=list_ids,
        student_mark_list_usecase=list_marks,
        target_id=TargetID(1),
    )
    path = tmp_path / "scores.xlsx"
    path.touch()
    dialog._le_excel_fullpath.setText(str(path))
    dialog._dl_sheet_names.addItem("Sheet1")
    return dialog, ids, list_marks, has_data, apply


def test_export_rejects_unmarked_including_zero_and_excluded_independent(
        qt_app: QApplication, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """未採点者がいれば出力せず、0点は採点済みとして扱う。"""
    first = StudentID("21D5109047B")
    second = StudentID("24A0007521M")
    dialog, ids, list_marks, has_data, apply = _dialog(
        tmp_path, [StudentMark(first, 0), StudentMark(second, None)]
    )
    warning = Mock()
    monkeypatch.setattr(QMessageBox, "warning", warning)
    dialog._ScoreExportDialog__b_export_clicked()
    warning.assert_called_once()
    assert str(second) in warning.call_args.args[2]
    has_data.execute.assert_not_called()
    apply.execute.assert_not_called()
    assert list_marks.execute.call_count == 1
    dialog.close()


def test_export_refetches_latest_marks_and_preserves_backup_setting(
        qt_app: QApplication, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ダイアログを開いた後の点数変更を出力に反映する。"""
    first = StudentID("21D5109047B")
    second = StudentID("24A0007521M")
    dialog, ids, list_marks, has_data, apply = _dialog(
        tmp_path, [StudentMark(first, 0), StudentMark(second, 90)]
    )
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.No)
    dialog._ScoreExportDialog__b_export_clicked()
    assert list_marks.execute.call_count == 1
    kwargs = apply.execute.call_args.kwargs
    assert [mark.student_id for mark in kwargs["student_marks"]] == ids
    assert [mark.score for mark in kwargs["student_marks"]] == [0, 90]
    assert kwargs["do_backup"] is True
    dialog.close()


def test_export_rejects_missing_mark_record(
        qt_app: QApplication, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """採点結果の一覧に学生が欠けていても書き込まない。"""
    first = StudentID("21D5109047B")
    dialog, ids, list_marks, has_data, apply = _dialog(
        tmp_path, [StudentMark(first, 50)]
    )
    warning = Mock()
    monkeypatch.setattr(QMessageBox, "warning", warning)
    dialog._ScoreExportDialog__b_export_clicked()
    warning.assert_called_once()
    has_data.execute.assert_not_called()
    apply.execute.assert_not_called()
    dialog.close()
