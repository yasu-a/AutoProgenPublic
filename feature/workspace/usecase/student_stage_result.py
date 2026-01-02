from typing import Callable

from feature.workspace.usecase.interface import IStudentStageResultClearUseCase
from shared.domain.error import StopTask
from shared.domain.service.student_stage_path_result import StudentStagePathResultEntityClearService
from shared.domain.value.identifier import StudentID


class StudentStageResultClearUseCase(IStudentStageResultClearUseCase):
    def __init__(
            self,
            *,
            student_stage_result_clear_service: StudentStagePathResultEntityClearService,
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
