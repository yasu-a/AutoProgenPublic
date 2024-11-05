from application.dependency.usecases import get_student_run_next_stage_usecase
from infra.tasks.task import AbstractStudentTask


class RunStagesStudentTask(AbstractStudentTask):
    def run(self):
        self._logger.info(f"Task started [{self.student_id}]")
        get_student_run_next_stage_usecase().execute(self._student_id)
