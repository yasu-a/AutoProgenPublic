from application.dependency import get_project_service, get_build_service, get_compile_service, \
    get_execute_service
from domain.models.stages import StudentProgressStage
from tasks.tasks import AbstractStudentTask


class RunStagesStudentTask(AbstractStudentTask):
    def _dispatch_stage(self, stage: StudentProgressStage):
        if stage == StudentProgressStage.BUILD:
            self._logger.info(f"Dispatching stage: {stage!r}")
            service = get_build_service()
            service.build_and_save_result(student_id=self._student_id)
        elif stage == StudentProgressStage.COMPILE:
            self._logger.info(f"Dispatching stage: {stage!r}")
            service = get_compile_service()
            service.compile_and_save_result(student_id=self._student_id)
        elif stage == StudentProgressStage.EXECUTE:
            self._logger.info(f"Dispatching stage: {stage!r}")
            service = get_execute_service()
            service.execute_and_save_result(student_id=self._student_id)
        else:
            self._logger.info(f"Not implemented stage: {stage!r}")

    def run(self):
        self._logger.info(f"Task started [{self.student_id}]")
        project_service = get_project_service()
        while True:
            # 現在の状況から次のステージを取得する
            next_stage = project_service.determine_student_next_stage_with_result(
                student_id=self._student_id,
            )
            # すべてのステージが終了したら終了
            if next_stage is None:
                self._logger.info("Task finished: all stages are finished")
                return
            self._logger.info(f"Task stage started:\n{next_stage=}")
            # ステージを始める前にそのステージ以降のデータが初期化されていることを保証する
            project_service.clear_student_to_start_stage(
                student_id=self._student_id,
                stage=next_stage,
            )
            # ステージを実行
            self._dispatch_stage(next_stage)
            # 現在の進捗を取得してエラーなら終了
            progress = project_service.get_student_progress(self._student_id)
            if not progress.is_success():
                self._logger.error(f"Task finished: stage error\n{progress=!r}")
                return


class CleanAllStagesStudentTask(AbstractStudentTask):
    def run(self) -> None:
        self._logger.info(f"Task started [{self.student_id}]")
        project_service = get_project_service()
        project_service.clear_all_stages_of_student(student_id=self._student_id)
        self._logger.info("Task finished: student data cleaned")
