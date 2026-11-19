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
    usecase = StudentMarkListUseCase(
        student_mark_list_service=service,
        project_settings_get_usecase=Mock(),
    )

    actual = usecase.execute(student_ids=(third, second))

    assert [student_mark.student_id for student_mark in actual] == [second, third]


def test_returns_all_marks_when_student_ids_are_omitted() -> None:
    """学生IDを省略した場合は全採点結果をそのまま返す。"""
    student_id = StudentID("21D5109047B")
    expected = [StudentMark(student_id, 90)]
    service = Mock()
    service.execute.return_value = expected
    usecase = StudentMarkListUseCase(
        student_mark_list_service=service,
        project_settings_get_usecase=Mock(),
    )

    assert usecase.execute() == expected


def test_scoring_student_ids_preserve_order_and_exclude_skipped() -> None:
    """指定なし・対象学生の指定では、除外者を除いた全員を元の順序で返す。"""
    first = StudentID("21D5109047B")
    second = StudentID("24A0007521M")
    third = StudentID("25B0000001C")
    service = Mock()
    service.execute.return_value = [
        StudentMark(first, 10),
        StudentMark(second, 20),
        StudentMark(third, 30),
    ]
    settings = Mock()
    settings.execute.return_value.bulk_grading_skips = frozenset({second})
    usecase = StudentMarkListUseCase(
        student_mark_list_service=service,
        project_settings_get_usecase=settings,
    )

    assert usecase.list_scoring_student_ids() == [first, third]
    assert usecase.list_scoring_student_ids(selected_student_id=third) == [first, third]
    assert usecase.list_scoring_student_ids(selected_student_id=second) == [second]
    assert usecase.list_scoring_student_ids(
        selected_student_id=StudentID("26C0000002D"),
    ) == []


def test_scoring_student_ids_with_no_targets() -> None:
    """全員除外時は通常採点の対象がなく、除外者の単独表示だけ可能。"""
    student_id = StudentID("21D5109047B")
    service = Mock()
    service.execute.return_value = [StudentMark(student_id, 0)]
    settings = Mock()
    settings.execute.return_value.bulk_grading_skips = frozenset({student_id})
    usecase = StudentMarkListUseCase(
        student_mark_list_service=service,
        project_settings_get_usecase=settings,
    )

    assert usecase.list_scoring_student_ids() == []
    assert usecase.list_scoring_student_ids(selected_student_id=student_id) == [student_id]
    service.execute.return_value = []
    assert usecase.list_scoring_student_ids(selected_student_id=student_id) == []
