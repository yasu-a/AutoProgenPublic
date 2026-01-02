from shared.domain.entity.student_mark import StudentMarkEntity
from shared.domain.service.student_mark_get import StudentMarkEntityGetSubService
from shared.infra.repository.student import StudentRepository


class StudentMarkEntityListService:
    def __init__(
            self,
            *,
            student_repo: StudentRepository,
            student_mark_get_sub_service: StudentMarkEntityGetSubService,
    ):
        self._student_repo = student_repo
        self._student_mark_get_sub_service = student_mark_get_sub_service

    def execute(self) -> list[StudentMarkEntity]:
        student_marks = []
        for student_entity in self._student_repo.list():
            student_mark = self._student_mark_get_sub_service.execute(student_entity.student_id)
            student_marks.append(student_mark)
        return student_marks
