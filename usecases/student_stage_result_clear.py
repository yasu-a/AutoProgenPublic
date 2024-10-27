from domain.models.values import StudentID
from services.student_stage_result import StudentStageResultClearService


class StudentStageResultClearUseCase:
    def __init__(
            self,
            *,
            student_stage_result_clear_service: StudentStageResultClearService,
    ):
        self._student_stage_result_clear_service = student_stage_result_clear_service

    def execute(self, student_id: StudentID) -> None:
        self._student_stage_result_clear_service.execute(
            student_id=student_id,
        )
