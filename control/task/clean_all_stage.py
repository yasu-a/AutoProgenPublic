from domain.error import StopTask
from infra.task.task import AbstractStudentTask
from usecase.student_stage_result import StudentStageResultClearUseCase

class CleanAllStagesStudentTask(AbstractStudentTask):
    def __init__(
            self,
            parent,
            student_id,
            *,
            student_stage_result_clear_usecase: StudentStageResultClearUseCase,
    ):
        super().__init__(parent, student_id)
        self._student_stage_result_clear_usecase = student_stage_result_clear_usecase

    def run(self) -> None:
        self._logger.info(f"Task started [{self.student_id}]")
        try:
            self._student_stage_result_clear_usecase.execute(
                student_id=self.student_id,
                stop_producer=self.is_stop_received,
            )
        except StopTask:
            self._logger.info(f"Task stopped: [{self.student_id}]")
        else:
            self._logger.info("Task finished: student data cleaned")

    def __repr__(self):
        return f"CleanAllStagesStudentTask(student_id={self.student_id!r})"

    def __str__(self):
        return f"クリア {self.student_id}"
