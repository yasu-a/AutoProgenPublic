from domain.model.value import StudentID
from service.student_dynamic import StudentDynamicGetSourceContentService


class StudentSourceCodeGetUseCase:
    def __init__(
            self,
            *,
            student_source_code_get_query_service: StudentDynamicGetSourceContentService,
    ):
        self._student_source_code_get_query_service = student_source_code_get_query_service

    def execute(self, student_id: StudentID) -> str | None:
        try:
            source_code = self._student_source_code_get_query_service.execute(student_id)
        except FileNotFoundError:
            return None
        else:
            return source_code
