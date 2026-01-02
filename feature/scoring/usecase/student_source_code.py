from feature.scoring.usecase.interface import IStudentSourceCodeGetUseCase
from shared.domain.value.identifier import StudentID
from shared.infra.repository.student_dynamic import StudentSourceRepository


class StudentSourceCodeGetUseCase(IStudentSourceCodeGetUseCase):
    def __init__(
            self,
            *,
            student_source_repo: StudentSourceRepository,
    ):
        self._student_source_repo = student_source_repo

    def execute(self, student_id: StudentID) -> str | None:
        try:
            if not self._student_source_repo.exists(student_id):
                return None
            source_code = self._student_source_repo.get(student_id).content_text
        except FileNotFoundError:
            return None
        else:
            return source_code
