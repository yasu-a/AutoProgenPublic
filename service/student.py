from domain.model.student import Student
from domain.model.value import StudentID
from infra.repository.student import StudentRepository


class StudentGetService:
    def __init__(
            self,
            *,
            student_repo: StudentRepository,
    ):
        self._student_repo = student_repo

    def execute(self, student_id: StudentID) -> Student:
        return self._student_repo.get(student_id)


class StudentListSubService:
    def __init__(
            self,
            *,
            student_repo: StudentRepository,
    ):
        self._student_repo = student_repo

    def execute(self) -> list[Student]:
        return self._student_repo.list()
