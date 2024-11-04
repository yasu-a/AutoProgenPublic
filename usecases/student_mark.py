from domain.models.student_mark import StudentMark
from domain.models.values import StudentID
from services.student_mark import StudentMarkGetSubService, StudentMarkPutService, \
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

    def execute(self) -> list[StudentMark]:
        return self._student_mark_list_service.execute()
