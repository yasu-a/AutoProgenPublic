"""採点結果一覧の検索条件を検証する。"""

from unittest.mock import Mock

from autoprogen.domain.model.student_mark import StudentMark
from autoprogen.domain.model.value import StudentID
from autoprogen.usecase.student_mark import StudentMarkListUseCase


def test_filters_marks_by_student_ids_and_confirmation() -> None:
    """学生IDと確定状態をAND条件で絞り、元の一覧順を維持する。"""
    first = StudentID("21D5109047B")
    second = StudentID("24A0007521M")
    third = StudentID("25B0000001C")
    service = Mock()
    service.execute.return_value = [
        StudentMark(first, 90, confirmed=True),
        StudentMark(second, 80, confirmed=False),
        StudentMark(third, None),
    ]
    usecase = StudentMarkListUseCase(student_mark_list_service=service)

    actual = usecase.execute(
        student_ids=(third, second),
        confirmed=False,
    )

    assert [student_mark.student_id for student_mark in actual] == [second, third]


def test_returns_all_marks_when_filters_are_omitted() -> None:
    """検索条件を省略した場合は従来どおり全採点結果を返す。"""
    student_id = StudentID("21D5109047B")
    expected = [StudentMark(student_id, 90, confirmed=True)]
    service = Mock()
    service.execute.return_value = expected
    usecase = StudentMarkListUseCase(student_mark_list_service=service)

    assert usecase.execute() == expected
