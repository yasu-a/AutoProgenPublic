from collections.abc import Iterable

from autoprogen.domain.model.student_mark import StudentMark
from autoprogen.domain.model.value import StudentID
from autoprogen.service.student_mark import StudentMarkGetSubService, StudentMarkPutService, \
    StudentMarkListService


class StudentMarkGetUseCase:
    def __init__(
            self,
            *,
            student_mark_get_sub_service: StudentMarkGetSubService,
    ):
        self._student_mark_get_sub_service = student_mark_get_sub_service

    def execute(self, student_id: StudentID) -> StudentMark:
        return self._student_mark_get_sub_service.execute(student_id)


class StudentMarkPutUseCase:
    def __init__(
            self,
            *,
            student_mark_put_service: StudentMarkPutService,
    ):
        self._student_mark_put_service = student_mark_put_service

    def execute(self, student_mark: StudentMark) -> None:
        self._student_mark_put_service.execute(student_mark)


class StudentMarkListUseCase:
    def __init__(
            self,
            *,
            student_mark_list_service: StudentMarkListService,
    ):
        self._student_mark_list_service = student_mark_list_service

    def execute(
            self,
            *,
            student_ids: Iterable[StudentID] | None = None,
    ) -> list[StudentMark]:
        """指定された学生IDに一致する採点結果を元の一覧順で返す。"""
        student_marks = self._student_mark_list_service.execute()

        if student_ids is not None:
            target_student_ids = frozenset(student_ids)
            student_marks = [
                student_mark
                for student_mark in student_marks
                if student_mark.student_id in target_student_ids
            ]

        return student_marks
