from domain.models.student import Student
from domain.models.student_master import StudentMaster
from domain.models.values import StudentID
from infra.repositories.student import StudentRepository


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

    def execute(self) -> StudentMaster:
        return self._student_repo.list()
