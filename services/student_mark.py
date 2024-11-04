from domain.models.student_mark import StudentMark
from domain.models.values import StudentID
from infra.repositories.student_mark import StudentMarkRepository


class StudentMarkGetService:
    def __init__(
            self,
            *,
            student_mark_repo: StudentMarkRepository,
    ):
        self._student_mark_repo = student_mark_repo

    def execute(self, student_id: StudentID) -> StudentMark:
        return self._student_mark_repo.get(student_id)


class StudentMarkPutService:
    def __init__(
            self,
            *,
            student_mark_repo: StudentMarkRepository,
    ):
        self._student_mark_repo = student_mark_repo

    def execute(self, student_mark: StudentMark) -> None:
        self._student_mark_repo.put(student_mark)
