"""採点画面の点数入力を検証する。"""

import pytest
from PyQt5.QtWidgets import QApplication

from autoprogen.control.widget_mark_score_edit import MarkScoreEditWidget
from autoprogen.domain.model.student_mark import StudentMark
from autoprogen.domain.model.value import StudentID


@pytest.fixture
def qt_app(monkeypatch: pytest.MonkeyPatch) -> QApplication:
    """画面を表示せずに利用できるQApplicationを返す。"""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.mark.parametrize(("text", "score"), [("", None), ("0", 0), ("80", 80)])
def test_score_edit_distinguishes_empty_zero_and_score(
        qt_app: QApplication,
        text: str,
        score: int | None,
) -> None:
    """空欄・0点・通常点を区別して採点結果を返す。"""
    student_id = StudentID("21D5109047B")
    widget = MarkScoreEditWidget()
    widget.set_data(StudentMark(student_id, 50))

    widget._le_score.setText(text)
    actual = widget.get_data()

    assert actual is not None
    assert actual.student_id == student_id
    assert actual.score == score


def test_score_edit_tracks_changes_and_clear(qt_app: QApplication) -> None:
    """読込直後は未変更で、点数変更とクリアを変更として扱う。"""
    widget = MarkScoreEditWidget()
    widget.set_data(StudentMark(StudentID("21D5109047B"), 50))
    assert not widget.is_modified()

    widget._le_score.setText("80")
    assert widget.is_modified()
    assert widget.get_data().score == 80

    widget.set_unmarked()
    assert widget.get_data().score is None


def test_none_disables_score_edit(qt_app: QApplication) -> None:
    """学生が未指定の場合は点数入力とクリアを無効にする。"""
    widget = MarkScoreEditWidget()
    widget.set_data(None)

    assert widget.get_data() is None
    assert not widget._le_score.isEnabled()
    assert not widget._b_unmark.isEnabled()
