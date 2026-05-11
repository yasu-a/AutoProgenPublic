from domain.error import StopTask
from infra.task.task import AbstractStudentTask
from usecase.student_run_next_stage import StudentRunNextStageUseCase

class RunStagesStudentTask(AbstractStudentTask):
    def __init__(self, parent, student_id, *, student_run_next_stage_usecase: StudentRunNextStageUseCase):
        super().__init__(parent, student_id)
        self._student_run_next_stage_usecase = student_run_next_stage_usecase

    def run(self):
        self._logger.info(f"Task started [{self.student_id}]")
        try:
            self._student_run_next_stage_usecase.execute(
                student_id=self._student_id,
                stop_producer=self.is_stop_received,
            )
        except StopTask:
            self._logger.info(f"Task stopped [{self.student_id}]")

    def __repr__(self):
        return f"RunStagesStudentTask(student_id={self.student_id!r})"

    def __str__(self):
        return f"実行 {self.student_id}"
