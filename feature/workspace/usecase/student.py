from feature.workspace.usecase.interface import IStudentListIDUseCase
from shared.domain.entity.student import StudentEntity
from shared.domain.value.identifier import StudentID
from shared.infra.repository.student import StudentRepository


class StudentListIDUseCase(IStudentListIDUseCase):
    def __init__(
            self,
            *,
            student_repo: StudentRepository,
    ):
        self._student_repo = student_repo

    def execute(self) -> list[StudentID]:
        students: list[StudentEntity] = self._student_repo.list()
        return [student.student_id for student in students]
