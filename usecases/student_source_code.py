from domain.models.values import StudentID
from services.student_source_code import StudentSourceCodeGetQueryService


class StudentSourceCodeGetUseCase:
    def __init__(
            self,
            *,
            student_source_code_get_query_service: StudentSourceCodeGetQueryService,
    ):
        self._student_source_code_get_query_service = student_source_code_get_query_service

    def execute(self, student_id: StudentID) -> str | None:
        try:
            source_code = self._student_source_code_get_query_service.execute(student_id)
        except FileNotFoundError:
            return None
        else:
            return source_code
