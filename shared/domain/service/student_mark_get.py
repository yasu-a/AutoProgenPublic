from shared.domain.entity.student_mark import StudentMarkEntity
from shared.domain.interface.service import IStudentMarkEntityGetSubService
from shared.domain.value.identifier import StudentID
from shared.infra.repository.student_mark import StudentScoreRepository


class StudentMarkEntityGetSubService(IStudentMarkEntityGetSubService):
    def __init__(
            self,
            *,
            student_mark_repo: StudentScoreRepository,
    ):
        self._student_mark_repo = student_mark_repo

    def execute(self, student_id: StudentID) -> StudentMarkEntity:
        if not self._student_mark_repo.exists(student_id):
            return self._student_mark_repo.create(student_id)
        return self._student_mark_repo.get(student_id)
