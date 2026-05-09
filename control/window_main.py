from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from application.dependency.task import get_task_manager
from application.dependency.usecase import get_current_project_summary_get_usecase, \
    get_student_list_id_usecase, get_student_submission_folder_show_usecase
from control.dialog_mark import MarkDialog
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


class MainWindow(QMainWindow):
    _logger = create_logger()

    def __init__(
            self,
            parent: QObject = None,
            *,
            navigator: INavigator,
    ):
        super().__init__(parent)
        self._navigator = navigator

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        project_summary = get_current_project_summary_get_usecase().execute()

        # noinspection PyUnresolvedReferences
        self.setWindowTitle(
            f"{project_summary.project_name} 設問{project_summary.target_number}"
        )
        self.resize(1500, 800)

        # ツールバー
        self._tool_bar = ToolBar(self)
        # noinspection PyUnresolvedReferences
        self.addToolBar(self._tool_bar)

        # 生徒のテーブル
        # noinspection PyTypeChecker
        self._w_student_table = StudentTableWidget(self)
        # noinspection PyUnresolvedReferences
        self.setCentralWidget(self._w_student_table)

        # ステータスバー
        #  - タスクモニタ
        # noinspection PyTypeChecker
        self._sb_task_state = TaskStateStatusBarWidget(self)
        # noinspection PyUnresolvedReferences
        self.statusBar().addPermanentWidget(self._sb_task_state)
        # noinspection PyUnresolvedReferences
        self.statusBar().addPermanentWidget(QLabel(self), 1)
        #  - テスト版通知
        # noinspection PyTypeChecker
        self._sb_unstable_version_notif = UnstableVersionNotificationStatusBarWidget(self)
        # noinspection PyUnresolvedReferences
        self.statusBar().addPermanentWidget(self._sb_unstable_version_notif)
        #  - リソースモニタ
        # noinspection PyTypeChecker
        self._sb_process_resource_usage = ProcessResourceUsageStatusBarWidget(self)
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
        get_student_submission_folder_show_usecase().execute(
            student_id=student_id,
        )

    @pyqtSlot(StudentID)
    def __w_student_table_mark_result_cell_triggered(self, student_id: StudentID):
        # テーブルの生徒の点数がクリックされたとき
        # 生徒ごとの採点画面を開く
        if not get_task_manager().is_empty():
            # noinspection PyTypeChecker
            QMessageBox.warning(
                self,
                "採点",
                "実行が完了するまでは採点できません"
            )
            return

        dialog = MarkDialog(self)
        dialog.set_state(dialog.states.create_state_by_student_id(student_id))
        dialog.exec_()

    def __perform_stop_tasks(self):
        if not get_task_manager().is_empty():
            AbstractProgressDialog.run_blocking_task(
                parent=self,
                title="タスクの停止",
                initial_message="停止処理を開始します...",
                task_func=get_task_manager().terminate,
            )

    @classmethod
    def __enqueue_student_tasks_if_not_run(cls, parent, task_cls: type[AbstractStudentTask]):
        if not get_task_manager().is_empty():
            return
        for student_id in get_student_list_id_usecase().execute():
            get_task_manager().enqueue(
                task_cls(
                    parent=parent,
                    student_id=student_id,
                )
            )

    def __perform_reopen_project(self) -> None:
        # noinspection PyTypeChecker
        if QMessageBox.question(
                self,
                "プロジェクトを開く",
                "別のプロジェクトを開きます。このプロジェクトを閉じてもよろしいですか？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
        ) != QMessageBox.Yes:
            return
        self.close()

    def __tool_bar_triggered(self, name):
        self._tool_bar.update_button_state(is_task_alive=True)
        if name == "open-project":
            self.__perform_reopen_project()
        elif name == "run":
            self.__enqueue_student_tasks_if_not_run(
                parent=self,
                task_cls=RunStagesStudentTask,
            )
        elif name == "stop":
            self.__perform_stop_tasks()
        elif name == "clear":
            self.__enqueue_student_tasks_if_not_run(
                parent=self,
                task_cls=CleanAllStagesStudentTask,
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
        evt.accept()
        # noinspection PyTypeChecker
        QTimer.singleShot(
            0,
            lambda: self._navigator.transition_from_workspace_to_launcher(self),
        )
