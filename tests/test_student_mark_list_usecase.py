"""採点結果一覧の検索条件を検証する。"""

from unittest.mock import Mock

from autoprogen.domain.model.student_mark import StudentMark
from autoprogen.domain.model.value import StudentID
from autoprogen.usecase.student_mark import StudentMarkListUseCase


def test_filters_marks_by_student_ids_preserving_original_order() -> None:
    """指定された学生だけを元の一覧順を維持して返す。"""
    first = StudentID("21D5109047B")
    second = StudentID("24A0007521M")
    third = StudentID("25B0000001C")
    service = Mock()
    service.execute.return_value = [
        StudentMark(first, 90),
        StudentMark(second, 80),
        StudentMark(third, None),
    ]
    usecase = StudentMarkListUseCase(student_mark_list_service=service)

    actual = usecase.execute(student_ids=(third, second))

    assert [student_mark.student_id for student_mark in actual] == [second, third]


def test_returns_all_marks_when_student_ids_are_omitted() -> None:
    """学生IDを省略した場合は全採点結果をそのまま返す。"""
    student_id = StudentID("21D5109047B")
    expected = [StudentMark(student_id, 90)]
    service = Mock()
    service.execute.return_value = expected
    usecase = StudentMarkListUseCase(student_mark_list_service=service)

    assert usecase.execute() == expected
