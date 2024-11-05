from application.dependency.usecases import get_student_stage_result_clear_usecase
from infra.tasks.task import AbstractStudentTask


class CleanAllStagesStudentTask(AbstractStudentTask):
    def run(self) -> None:
        self._logger.info(f"Task started [{self.student_id}]")
        get_student_stage_result_clear_usecase().execute(self.student_id)
        self._logger.info("Task finished: student data cleaned")
