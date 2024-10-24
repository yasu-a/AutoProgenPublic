from domain.models.values import StudentID
from files.repositories.student import StudentRepository


class StudentSubmissionExistService:
    def __init__(
            self,
            *,
            student_repo: StudentRepository,
    ):
        self._student_repo = student_repo

    def execute(self, student_id: StudentID) -> bool:
        return self._student_repo.get(student_id).is_submitted
