from autoprogen.domain.model.source_code import SourceCode
from autoprogen.domain.model.value import StudentID
from autoprogen.service.student_dynamic import StudentDynamicGetSourceCodeService


class StudentSourceCodeGetUseCase:
    """採点画面へ学生の正規化済みソースコードを提供する。"""

    def __init__(
            self,
            *,
            student_dynamic_get_source_code_service: StudentDynamicGetSourceCodeService,
    ):
        self._student_dynamic_get_source_code_service = (
            student_dynamic_get_source_code_service
        )

    def execute(self, student_id: StudentID) -> SourceCode | None:
        """学生のソースコードを返し、未生成の場合はNoneを返す。"""
        try:
            source_code = self._student_dynamic_get_source_code_service.execute(
                student_id
            )
        except FileNotFoundError:
            return None
        else:
            return source_code
