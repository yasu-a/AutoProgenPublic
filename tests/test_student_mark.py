"""採点状態のドメインモデルを検証する。"""

import pytest

from autoprogen.domain.model.student_mark import StudentMark
from autoprogen.domain.model.value import StudentID


@pytest.fixture
def student_id() -> StudentID:
    """テスト用の学生IDを返す。"""
    return StudentID("21D5109047B")


def test_unmarked_is_unconfirmed(student_id: StudentID) -> None:
    """未採点は未確定であり、点数はNoneとして読める。"""
    mark = StudentMark(student_id=student_id, score=None)
    assert mark.student_id == student_id
    assert mark.score is None
    assert not mark.marked
    assert not mark.confirmed


@pytest.mark.parametrize("score", [0, 50, 99])
def test_marked_requires_explicit_confirmation(
        student_id: StudentID,
        score: int,
) -> None:
    """点数がある場合は確定状態の明示を必須とする。"""
    with pytest.raises(ValueError, match="confirmed is required"):
        StudentMark(student_id=student_id, score=score)

    mark = StudentMark(student_id=student_id, score=score, confirmed=True)
    assert mark.score == score
    assert mark.marked
    assert mark.confirmed


def test_marked_can_be_unconfirmed(student_id: StudentID) -> None:
    """点数を持った未確定状態を明示的に作成できる。"""
    mark = StudentMark(student_id=student_id, score=50, confirmed=False)
    assert mark.marked
    assert mark.score == 50
    assert not mark.confirmed


def test_cannot_construct_confirmed_unmarked(student_id: StudentID) -> None:
    """点数がない学生の確定状態を作成できない。"""
    with pytest.raises(ValueError, match="Cannot confirm an unmarked student"):
        StudentMark(student_id=student_id, score=None, confirmed=True)


def test_cannot_confirm_unmarked(student_id: StudentID) -> None:
    """未採点に対する確定操作は失敗し、元の状態を保持する。"""
    mark = StudentMark(student_id=student_id, score=None)
    with pytest.raises(ValueError, match="Cannot confirm an unmarked student"):
        mark.confirmed = True
    assert mark.score is None
    assert not mark.confirmed


def test_confirmation_can_be_toggled(student_id: StudentID) -> None:
    """採点済みなら点数を保持したまま確定を解除・設定できる。"""
    mark = StudentMark(student_id=student_id, score=50, confirmed=True)
    mark.confirmed = False
    assert mark.score == 50
    assert mark.marked
    assert not mark.confirmed
    mark.confirmed = True
    assert mark.confirmed


def test_score_update_preserves_confirmation_and_clearing_unmarks(
        student_id: StudentID,
) -> None:
    """点数変更では確定状態を維持し、Noneへの変更で確定を解除する。"""
    mark = StudentMark(student_id=student_id, score=20, confirmed=False)
    mark.score = 0
    assert mark.score == 0
    assert mark.marked
    assert not mark.confirmed
    mark.confirmed = True
    mark.score = 75
    assert mark.confirmed
    mark.score = None
    assert mark.score is None
    assert not mark.marked
    assert not mark.confirmed
    mark.score = 75
    assert mark.score == 75
    assert not mark.confirmed


def test_repr_includes_confirmation(student_id: StudentID) -> None:
    """デバッグ表示に確定状態を含む。"""
    mark = StudentMark(student_id=student_id, score=50, confirmed=False)
    assert "score=50" in repr(mark)
    assert "confirmed=False" in repr(mark)
