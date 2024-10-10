from domain.models.student_master import StudentMaster
from files.repositories.student import StudentRepository


class StudentListService:
    def __init__(
            self,
            *,
            student_master_repo: StudentRepository,
    ):
        self._student_repo = student_master_repo

    def execute(self) -> StudentMaster:
        return self._student_repo.list()
