"""採点画面の点数入力と確定状態の関係を検証する。"""

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


@pytest.mark.parametrize("confirmed", [False, True])
def test_score_edit_preserves_loaded_confirmation(
        qt_app: QApplication,
        confirmed: bool,
) -> None:
    """点数を編集しても読み込んだ確定状態を暗黙に変更しない。"""
    student_id = StudentID("21D5109047B")
    widget = MarkScoreEditWidget()
    widget.set_data(StudentMark(student_id, 50, confirmed=confirmed))

    widget._le_score.setText("80")
    actual = widget.get_data()

    assert actual is not None
    assert actual.score == 80
    assert actual.confirmed is confirmed


def test_reentering_score_after_clear_remains_unconfirmed(
        qt_app: QApplication,
) -> None:
    """点数を消して確定解除した後の再入力では自動確定しない。"""
    student_id = StudentID("21D5109047B")
    widget = MarkScoreEditWidget()
    widget.set_data(StudentMark(student_id, 50, confirmed=True))

    widget.set_unmarked()
    widget._le_score.setText("80")
    actual = widget.get_data()

    assert actual is not None
    assert actual.score == 80
    assert not actual.confirmed


def test_confirmation_changes_score_field_appearance(
        qt_app: QApplication,
) -> None:
    """確定済みだけを緑色で表示し、点数クリア時に通常表示へ戻す。"""
    student_id = StudentID("21D5109047B")
    widget = MarkScoreEditWidget()
    changes: list[bool] = []
    widget.confirmation_changed.connect(changes.append)

    widget.set_data(StudentMark(student_id, 50, confirmed=True))

    assert "#dffe8b" in widget._le_score.styleSheet()
    assert changes == [True]

    widget.set_unmarked()

    assert widget._le_score.styleSheet() == ""
    assert changes == [True, False]
