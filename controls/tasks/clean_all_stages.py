from application.dependency.usecases import get_student_stage_result_clear_usecase
from domain.errors import StopTask
from infra.tasks.task import AbstractStudentTask


class CleanAllStagesStudentTask(AbstractStudentTask):
    def run(self) -> None:
        self._logger.info(f"Task started [{self.student_id}]")
        try:
            get_student_stage_result_clear_usecase().execute(
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
