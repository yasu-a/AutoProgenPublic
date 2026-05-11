from typing import TYPE_CHECKING, Callable

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from control.dialog_progress import AbstractProgressDialog
from control.task.clean_all_stage import CleanAllStagesStudentTask
from control.task.run_stage import RunStagesStudentTask
from control.widget_status_process_resource_usage import ProcessResourceUsageStatusBarWidget
from control.widget_status_task_state import TaskStateStatusBarWidget
from control.widget_status_unstable_version_notif import UnstableVersionNotificationStatusBarWidget
from control.widget_student_table import StudentTableWidget
from control.widget_toolbar import ToolBar
from domain.model.value import StudentID
from infra.task.task import AbstractStudentTask
from util.app_logging import create_logger

from control.interface_navigator import INavigator

if TYPE_CHECKING:
    from application.container import ProjectContainer, AppContainer


class MainWindow(QMainWindow):
    _logger = create_logger()

    def __init__(
            self,
            parent: QObject = None,
            *,
            navigator: INavigator,
            app_container: "AppContainer",
            project_container: "ProjectContainer",
    ):
        super().__init__(parent)
        self._navigator = navigator
        self._app_container = app_container
        self._project_container = project_container
        self._task_manager = project_container.task_manager

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        project_summary = self._project_container.current_project_summary_get_usecase.execute()

        # noinspection PyUnresolvedReferences
        self.setWindowTitle(
            f"{project_summary.project_name} 設問{project_summary.target_number}"
        )
        self.resize(1500, 800)

        # ツールバー
        self._tool_bar = ToolBar(
            self,
            task_manager=self._task_manager,
        )
        # noinspection PyUnresolvedReferences
        self.addToolBar(self._tool_bar)

        # 生徒のテーブル
        # noinspection PyTypeChecker
        self._w_student_table = StudentTableWidget(
            self,
            student_list_id_usecase=self._project_container.student_list_id_usecase,
            student_dynamic_take_diff_snapshot_usecase=self._project_container.student_dynamic_take_diff_snapshot_usecase,
            student_table_get_student_id_cell_data_usecase=self._project_container.student_table_get_student_id_cell_data_usecase,
            student_table_get_student_name_cell_data_usecase=self._project_container.student_table_get_student_name_cell_data_usecase,
            student_table_get_student_stage_state_cell_data_usecase=self._project_container.student_table_get_student_stage_state_cell_data_usecase,
            student_table_get_student_error_cell_data_usecase=self._project_container.student_table_get_student_error_cell_data_usecase,
            student_mark_get_usecase=self._project_container.student_mark_get_usecase,
        )
        # noinspection PyUnresolvedReferences
        self.setCentralWidget(self._w_student_table)

        # ステータスバー
        #  - タスクモニタ
        # noinspection PyTypeChecker
        self._sb_task_state = TaskStateStatusBarWidget(
            self,
            task_manager=self._task_manager,
        )
        # noinspection PyUnresolvedReferences
        self.statusBar().addPermanentWidget(self._sb_task_state)
        # noinspection PyUnresolvedReferences
        self.statusBar().addPermanentWidget(QLabel(self), 1)
        #  - テスト版通知
        # noinspection PyTypeChecker
        self._sb_unstable_version_notif = UnstableVersionNotificationStatusBarWidget(
            self,
            app_container=self._app_container,
        )
        # noinspection PyUnresolvedReferences
        self.statusBar().addPermanentWidget(self._sb_unstable_version_notif)
        #  - リソースモニタ
        # noinspection PyTypeChecker
        self._sb_process_resource_usage = ProcessResourceUsageStatusBarWidget(
            self,
            app_container=self._app_container,
        )
        # noinspection PyUnresolvedReferences
        self.statusBar().addPermanentWidget(self._sb_process_resource_usage)

    def _init_signals(self):
        self._tool_bar.triggered.connect(self.__tool_bar_triggered)
        self._w_student_table.student_id_cell_triggered.connect(
            self.__w_student_table_student_id_cell_triggered
        )
        self._w_student_table.mark_result_cell_triggered.connect(
            self.__w_student_table_mark_result_cell_triggered
        )

    @pyqtSlot(StudentID)
    def __w_student_table_student_id_cell_triggered(self, student_id: StudentID):
        # テーブルの生徒の学籍番号がクリックされたとき
        # 学生の提出データがあるフォルダを開く
        self._project_container.student_submission_folder_show_usecase.execute(
            student_id=student_id,
        )

    @pyqtSlot(StudentID)
    def __w_student_table_mark_result_cell_triggered(self, student_id: StudentID):
        # テーブルの生徒の点数がクリックされたとき
        # 生徒ごとの採点画面を開く
        if not self._task_manager.is_empty():
            # noinspection PyTypeChecker
            QMessageBox.warning(
                self,
                "採点",
                "実行が完了するまでは採点できません"
            )
            return

        self._navigator.open_scoring_dialog_for_student(self, student_id)

    def __perform_stop_tasks(self):
        if not self._task_manager.is_empty():
            AbstractProgressDialog.run_blocking_task(
                parent=self,
                title="タスクの停止",
                initial_message="停止処理を開始します...",
                task_func=self._task_manager.terminate,
            )

    def __enqueue_student_tasks_if_not_run(self, task_factory: Callable[[StudentID], AbstractStudentTask]):
        if not self._task_manager.is_empty():
            return
        for student_id in self._project_container.student_list_id_usecase.execute():
            self._task_manager.enqueue(task_factory(student_id))

    def __tool_bar_triggered(self, name):
        self._tool_bar.update_button_state(is_task_alive=True)
        if name == "run":
            self.__enqueue_student_tasks_if_not_run(
                lambda student_id: RunStagesStudentTask(
                    parent=self,
                    student_id=student_id,
                    student_run_next_stage_usecase=self._project_container.student_run_next_stage_usecase,
                ),
            )
        elif name == "stop":
            self.__perform_stop_tasks()
        elif name == "clear":
            self.__enqueue_student_tasks_if_not_run(
                lambda student_id: CleanAllStagesStudentTask(
                    parent=self,
                    student_id=student_id,
                    student_stage_result_clear_usecase=self._project_container.student_stage_result_clear_usecase,
                ),
            )
        elif name == "edit-settings":
            # noinspection PyTypeChecker
            self._navigator.open_setting_dialog(self)
        elif name == "edit-testcases":
            # noinspection PyTypeChecker
            self._navigator.open_testcase_list_edit_dialog(self)
        elif name == "mark":
            # noinspection PyTypeChecker
            self._navigator.open_scoring_dialog(self)
        elif name == "export-scores":
            # noinspection PyTypeChecker
            self._navigator.open_score_export_dialog(self)
        elif name == "about":
            # noinspection PyTypeChecker
            self._navigator.open_about_dialog(self)
        else:
            assert False, name

    def closeEvent(self, evt, **kwargs):
        self._w_student_table.shutdown()
        evt.accept()
        # noinspection PyTypeChecker
        QTimer.singleShot(
            0,
            lambda: self._navigator.transition_from_workspace_to_launcher(self),
        )
