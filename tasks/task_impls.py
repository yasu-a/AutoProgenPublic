from domain.models.stages import StudentProgressStage
from service_provider import get_build_service, get_project_service, get_compile_service, \
    get_execute_service
from tasks.tasks import AbstractStudentTask


class StudentTask(AbstractStudentTask):
    def _clear_student_if_last_stage_error(self, force=False):
        project_service = get_project_service()
        if not force:
            progress = project_service.get_student_progress(self._student_id)
            if progress.is_success() is None:  # どのステージも完了していない
                return
            if progress.is_success() is True:  # 最後のステージが完了している
                return
        project_service.clear_student(self._student_id)

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
        self._logger.info("Task started")
        # TODO: レポートフォルダのハッシュをとって変更が加えられた学生も初期化を実行する！！！
        # TODO: テストケースのハッシュをとって変更が加えられた場合も初期化を実行する！！！
        self._clear_student_if_last_stage_error(force=True)  # TODO: デバッグ用にforce=True
        project_service = get_project_service()
        prev_stage = None
        while True:
            # TODO: もしくは条件に応じて現在の生徒のprogressを返し，
            #       あるステージが開始される時点で以降のフォルダが初期化されていることを保証する
            progress = project_service.get_student_progress(self._student_id)
            next_stage = progress.get_expected_next_stage()
            self._logger.info(f"Progress: {progress}")
            if next_stage is None or prev_stage == next_stage:
                break
            self._dispatch_stage(next_stage)
            prev_stage = next_stage
        self._logger.info("Task finished")
