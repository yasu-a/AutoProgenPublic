from PyQt5.QtCore import QTimer

from app.di.system import get_task_manager
from app.di.usecase import (
    get_current_project_summary_get_usecase,
    get_resource_usage_get_usecase,
    get_student_list_id_usecase,
)
from feature.workspace.handler.interface import IWorkspaceWindowHandler, IWorkspaceWindowView
from feature.workspace.task.clean_all_stage import CleanAllStagesStudentTask
from feature.workspace.task.run_stage import RunStagesStudentTask
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

        # リソース使用状況の更新タイマー
        self._resource_usage_timer = QTimer()
        self._resource_usage_timer.setInterval(1000)
        # noinspection PyUnresolvedReferences
        self._resource_usage_timer.timeout.connect(self._update_resource_usage)

    def on_view_initialized(self) -> None:
        """Viewが初期化されたときに呼ばれる"""
        # ウィンドウタイトルを設定
        project_summary = get_current_project_summary_get_usecase().execute()
        self._view.set_window_title(
            f"{project_summary.project_name} 設問{project_summary.target_number}"
        )

        # リソース使用状況の初回更新
        self._update_resource_usage()

        # タイマースタート
        self._resource_usage_timer.start()

    def on_view_closed(self) -> None:
        """Viewが閉じられるときの処理"""
        if self._resource_usage_timer.isActive():
            self._resource_usage_timer.stop()
            self._logger.debug("Resource usage timer stopped.")

    def _update_resource_usage(self) -> None:
        """リソース使用状況を更新"""
        result = get_resource_usage_get_usecase().execute()
        resource_usage_view = self._view.get_process_resource_usage_status_bar_view()
        resource_usage_view.set_resource_usage(
            cpu_percent=result.cpu_percent,
            memory_mega_bytes=result.memory_mega_bytes,
            disk_read_count=result.disk_read_count,
            disk_write_count=result.disk_write_count,
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
            self._navigator.wait_for_task_termination(
                parent=self._view.get_parent_widget(),
            )
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

    # --- 内部メソッド ---

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
