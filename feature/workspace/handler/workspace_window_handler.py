from PyQt5.QtWidgets import QMessageBox

from app.di.repository import get_current_project_repository
from app.di.system import get_task_manager
from app.di.usecase import (
    get_current_project_summary_get_usecase,
    get_student_list_id_usecase,
    get_student_submission_folder_show_usecase,
)
from feature.workspace.handler.interface import IWorkspaceWindowHandler, IWorkspaceWindowView
from feature.workspace.task.clean_all_stage import CleanAllStagesStudentTask
from feature.workspace.task.run_stage import RunStagesStudentTask
from feature.workspace.view.dialog_stop_tasks import StopTasksDialog
from shared.domain.value.identifier import StudentID
from shared.handler.interface import INavigator
from shared.infra.system.task import AbstractStudentTask
from util.app_logging import create_logger


class WorkspaceWindowHandler(IWorkspaceWindowHandler):
    """ワークスペースウィンドウ専任のHandler"""

    _logger = create_logger()

    def __init__(
            self,
            *,
            view: IWorkspaceWindowView,
            navigator: INavigator,
    ):
        self._view = view
        self._navigator = navigator

    def on_view_initialized(self) -> None:
        """Viewが初期化されたときに呼ばれる"""
        # ウィンドウタイトルを設定
        project_summary = get_current_project_summary_get_usecase().execute()
        self._view.set_window_title(
            f"{project_summary.project_name} 設問{project_summary.target_number}"
        )

    def on_toolbar_action_triggered(self, action_name: str) -> None:
        """ツールバーのアクションがトリガーされたとき"""
        if action_name == "open-ProjectEntity":
            # プロジェクトを開く機能は削除（Navigatorが管理する）
            pass
        elif action_name == "run":
            self._enqueue_student_tasks_if_not_run(
                parent=self._view.get_parent_widget(),
                task_cls=RunStagesStudentTask,
            )
        elif action_name == "stop":
            self._perform_stop_tasks()
        elif action_name == "clear":
            self._enqueue_student_tasks_if_not_run(
                parent=self._view.get_parent_widget(),
                task_cls=CleanAllStagesStudentTask,
            )
        elif action_name == "edit-setting":
            self._handle_edit_settings()
        elif action_name == "edit-testcases":
            self._handle_edit_testcases()
        elif action_name == "mark":
            self._handle_mark()
        elif action_name == "export-scores":
            self._handle_export_scores()
        elif action_name == "about":
            self._handle_about()
        else:
            assert False, action_name

    def on_student_id_cell_clicked(self, student_id: StudentID) -> None:
        """生徒の学籍番号セルがクリックされたとき"""
        # 学生の提出データがあるフォルダを開く
        get_student_submission_folder_show_usecase().execute(
            student_id=student_id,
        )

    def on_mark_result_cell_clicked(self, student_id: StudentID) -> None:
        """生徒の点数セルがクリックされたとき"""
        # タスクが実行中かチェック
        if not get_task_manager().is_empty():
            QMessageBox.warning(
                self._view.get_parent_widget(),
                "採点",
                "タスクが終了するまでは採点できません"
            )
            return

        # 採点ダイアログを表示（指定された生徒）
        self._navigator.open_scoring_dialog_with_student(self._view.get_parent_widget(), student_id)

    # --- 内部メソッド ---

    @classmethod
    def _perform_stop_tasks(cls):
        """タスクを停止する"""
        if not get_task_manager().is_empty():
            dialog = StopTasksDialog()
            dialog.exec_()

    @classmethod
    def _enqueue_student_tasks_if_not_run(cls, parent, task_cls: type[AbstractStudentTask]):
        """タスクが実行中でなければ、生徒タスクをエンキューする"""
        if not get_task_manager().is_empty():
            return
        for student_id in get_student_list_id_usecase().execute():
            get_task_manager().enqueue(
                task_cls(
                    parent=parent,
                    student_id=student_id,
                )
            )

    def _handle_edit_settings(self) -> None:
        """設定ダイアログを表示"""
        self._navigator.open_setting_dialog(self._view.get_parent_widget())

    def _handle_edit_testcases(self) -> None:
        """テストケース編集ダイアログを表示"""
        self._navigator.open_testcase_list_edit_dialog(self._view.get_parent_widget())

    def _handle_mark(self) -> None:
        """採点ダイアログを表示（最初の生徒）"""
        self._navigator.open_scoring_dialog(self._view.get_parent_widget())

    def _handle_export_scores(self) -> None:
        """点数エクスポートダイアログを表示"""
        from app.di.repository import get_current_project_repository
        target_id = get_current_project_repository().get().target_id
        self._navigator.open_score_export_dialog(self._view.get_parent_widget(), target_id)

    def _handle_about(self) -> None:
        """Aboutダイアログを表示"""
        self._navigator.open_about_dialog(self._view.get_parent_widget())
