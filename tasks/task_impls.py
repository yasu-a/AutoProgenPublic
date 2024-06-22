from models.errors import BuildServiceError, CompileServiceError
from models.stages import StudentProgressStage
from service_provider import get_build_service, get_project_service, get_compile_service
from tasks.tasks import AbstractStudentTask


class StudentTask(AbstractStudentTask):
    def _clear_student_if_error(self):
        project_service = get_project_service()
        progress = project_service.get_student_progress(self._student_id)
        if progress.is_success() is None:
            return
        if progress.is_success() is True:
            return
        project_service.clear_student(self._student_id)

    def _dispatch_stage(self, stage: StudentProgressStage):
        if stage == StudentProgressStage.BUILD:
            self._logger.info(f"Dispatching stage: {stage!r}")
            service = get_build_service()
            try:
                service.build_and_save_result(
                    student_id=self._student_id)
            except BuildServiceError as e:
                self._logger.exception(f"コンパイル環境の構築に失敗しました\n{e.reason}")
        elif stage == StudentProgressStage.COMPILE:
            self._logger.info(f"Dispatching stage: {stage!r}")
            service = get_compile_service()
            try:
                service.compile_and_save_result(student_id=self._student_id)
            except CompileServiceError as e:
                self._logger.exception(f"コンパイル環境の構築に失敗しました\n{e.reason}")
        else:
            self._logger.info(f"Not implemented stage: {stage!r}")

    def run(self):
        self._logger.info("TASK ENTER")
        self._clear_student_if_error()  # TODO: レポートフォルダのハッシュをとって変更が加えられた学生も初期化実行する！！！
        project_service = get_project_service()
        prev_stage = None
        while True:
            progress = project_service.get_student_progress(self._student_id)
            next_stage = progress.get_expected_next_stage()
            self._logger.info(f"Progress: {progress}")
            if next_stage is None or prev_stage == next_stage:
                break
            self._dispatch_stage(next_stage)
            prev_stage = next_stage
        self._logger.info("TASK EXIT")
