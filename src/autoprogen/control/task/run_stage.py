from autoprogen.domain.error import StopTask
from autoprogen.infra.task.task import AbstractStudentTask
from autoprogen.usecase.main_window import MainWindowFacade

class RunStagesStudentTask(AbstractStudentTask):
    """メイン画面から学生の未完了ステージを実行するタスク。"""

    def __init__(
            self,
            parent,
            student_id,
            *,
            main_window_facade: MainWindowFacade,
    ) -> None:
        """実行対象とメイン画面Facadeを受け取る。"""
        super().__init__(parent, student_id)
        self._main_window_facade = main_window_facade

    def run(self) -> None:
        """停止要求を監視しながら学生の未完了ステージを実行する。"""
        self._logger.info(f"Task started [{self.student_id}]")
        try:
            self._main_window_facade.run_student_next_stage(
                student_id=self._student_id,
                stop_producer=self.is_stop_received,
            )
        except StopTask:
            self._logger.info(f"Task stopped [{self.student_id}]")

    def __repr__(self) -> str:
        """デバッグ向けのタスク表現を返す。"""
        return f"RunStagesStudentTask(student_id={self.student_id!r})"

    def __str__(self) -> str:
        """画面表示向けのタスク名を返す。"""
        return f"実行 {self.student_id}"
