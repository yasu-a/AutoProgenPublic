"""採点結果のドメインモデルを検証する。"""

import pytest

from autoprogen.domain.model.student_mark import StudentMark
from autoprogen.domain.model.value import StudentID


@pytest.fixture
def student_id() -> StudentID:
    """テスト用の学生IDを返す。"""
    return StudentID("21D5109047B")


@pytest.mark.parametrize(
    ("score", "marked"),
    [(None, False), (0, True), (50, True), (99, True)],
)
def test_score_and_marked_contract(
        student_id: StudentID,
        score: int | None,
        marked: bool,
) -> None:
    """未採点・0点・通常点を区別して保持する。"""
    mark = StudentMark(student_id=student_id, score=score)

    assert mark.student_id == student_id
    assert mark.score == score
    assert mark.marked is marked


def test_score_can_be_updated_and_cleared(student_id: StudentID) -> None:
    """点数を変更でき、Noneへの変更で未採点へ戻る。"""
    mark = StudentMark(student_id=student_id, score=20)

    mark.score = 0
    assert mark.score == 0
    assert mark.marked

    mark.score = None
    assert mark.score is None
    assert not mark.marked

    mark.score = 75
    assert mark.score == 75
    assert mark.marked


def test_repr_includes_student_and_score(student_id: StudentID) -> None:
    """デバッグ表示に学生IDと点数を含む。"""
    mark = StudentMark(student_id=student_id, score=50)

    assert str(student_id) in repr(mark)
    assert "score=50" in repr(mark)
