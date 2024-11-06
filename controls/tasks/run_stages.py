from application.dependency.usecases import get_student_run_next_stage_usecase
from domain.errors import StopTask
from infra.tasks.task import AbstractStudentTask


class RunStagesStudentTask(AbstractStudentTask):
    def run(self):
        self._logger.info(f"Task started [{self.student_id}]")
        try:
            get_student_run_next_stage_usecase().execute(
                student_id=self._student_id,
                stop_producer=self.is_stop_received,
            )
        except StopTask:
            self._logger.info(f"Task stopped [{self.student_id}]")

    def __repr__(self):
        return f"RunStagesStudentTask(student_id={self.student_id!r})"

    def __str__(self):
        return f"実行 {self.student_id}"
