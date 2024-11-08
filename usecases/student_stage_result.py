from typing import Callable

from domain.errors import StopTask
from domain.models.values import StudentID
from services.student_stage_result import StudentStageResultClearService


class StudentStageResultClearUseCase:
    def __init__(
            self,
            *,
            student_stage_result_clear_service: StudentStageResultClearService,
    ):
        self._student_stage_result_clear_service = student_stage_result_clear_service

    def execute(
            self,
            *,
            student_id: StudentID,
            stop_producer: Callable[[], bool],  # 停止するときTrueを受け取る
    ) -> None:
        if stop_producer():
            raise StopTask()
        self._student_stage_result_clear_service.execute(
            student_id=student_id,
        )
