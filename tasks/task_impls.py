from application.dependency.usecases import get_student_run_next_stage_usecase
from tasks.tasks import AbstractStudentTask


class RunStagesStudentTask(AbstractStudentTask):
    # def _dispatch_stage(self, stage: AbstractStage):
    #     if stage == AbstractStage.BUILD:
    #         self._logger.info(f"Dispatching stage: {stage!r}")
    #         service = get_build_service()
    #         service.build_and_save_result(student_id=self._student_id)
    #     elif stage == AbstractStage.COMPILE:
    #         self._logger.info(f"Dispatching stage: {stage!r}")
    #         service = get_compile_service()
    #         service.compile_and_save_result(student_id=self._student_id)
    #     elif stage == AbstractStage.EXECUTE:
    #         self._logger.info(f"Dispatching stage: {stage!r}")
    #         service = get_execute_service()
    #         service.execute_and_save_result(student_id=self._student_id)
    #     elif stage == AbstractStage.TEST:
    #         self._logger.info(f"Dispatching stage: {stage!r}")
    #         service = get_test_service()
    #         service.test_and_save_result(student_id=self._student_id)
    #     else:
    #         self._logger.info(f"Not implemented stage: {stage!r}")

    def run(self):
        self._logger.info(f"Task started [{self.student_id}]")
        # while True:
        #     # 現在の状況から次のステージを取得する
        #     next_stage = project_service.determine_student_next_stage_with_result(
        #         student_id=self._student_id,
        #     )
        #     # すべてのステージが終了したら終了
        #     if next_stage is None:
        #         self._logger.info("Task finished: all stages are finished")
        #         return
        #     self._logger.info(f"Task stage started:\n{next_stage=}")
        #     # ステージを始める前にそのステージ以降のデータが初期化されていることを保証する
        #     project_service.clear_student_to_start_stage(
        #         student_id=self._student_id,
        #         stage=next_stage,
        #     )
        #     # ステージを実行
        #     self._dispatch_stage(next_stage)
        #     # 現在の進捗を取得してエラーなら終了
        #     progress = project_service.get_student_progress(self._student_id)
        #     if not progress.is_success():
        #         self._logger.error(f"Task finished: stage error\n{progress=!r}")
        #         return
        get_student_run_next_stage_usecase().execute(self._student_id)


class CleanAllStagesStudentTask(AbstractStudentTask):
    def run(self) -> None:
        self._logger.info(f"Task started [{self.student_id}]")
        get_progress_service().clear_all_stages_of_student(student_id=self._student_id)
        self._logger.info("Task finished: student data cleaned")
