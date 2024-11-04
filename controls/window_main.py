import psutil
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from app_logging import create_logger
from application.dependency.tasks import get_task_manager
from application.dependency.usecases import get_current_project_summary_get_usecase, \
    get_student_list_id_usecase, get_student_submission_folder_show_usecase
from controls.dialog_global_config import GlobalConfigEditDialog
from controls.dialog_mark import MarkDialog
from controls.dialog_score_export import ScoreExportDialog
from controls.dialog_testcase_list_edit import TestCaseListEditDialog
from controls.res.icons import icon
from controls.widget_student_table import StudentTableWidget
from controls.widget_toolbar import ToolBar
from domain.models.values import StudentID
from tasks.task_impls import RunStagesStudentTask, CleanAllStagesStudentTask
from tasks.tasks import AbstractStudentTask


def enqueue_student_tasks_if_not_run(parent, task_cls: type[AbstractStudentTask]):
    if get_task_manager().get_student_task_count() > 0:
        return
    for student_id in get_student_list_id_usecase().execute():
        get_task_manager().enqueue_student_task(
            task_cls(
                parent=parent,
                student_id=student_id,
            )
        )


class MainWindow(QMainWindow):
    _logger = create_logger()

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

        timer = QTimer(self)
        timer.setInterval(500)
        timer.timeout.connect(self.__status_info_update_timer_timeout)  # type: ignore
        timer.start()  # type: ignore
        self.__context_info_update_timer = timer

    def _init_ui(self):
        project_summary = get_current_project_summary_get_usecase().execute()

        # noinspection PyUnresolvedReferences
        self.setWindowTitle(
            f"Auto Progen {project_summary.project_name} 設問{project_summary.target_number}"
        )
        # noinspection PyUnresolvedReferences
        self.setWindowIcon(icon("title"))
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

    def _init_signals(self):
        self._tool_bar.triggered.connect(self.__tool_bar_triggered)
        self._w_student_table.student_id_cell_double_clicked.connect(
            self.__w_student_table_student_id_cell_double_clicked
        )
        self._w_student_table.mark_result_cell_double_clicked.connect(
            self.__w_student_table_mark_result_cell_double_clicked
        )

    @pyqtSlot(StudentID)
    def __w_student_table_student_id_cell_double_clicked(self, student_id: StudentID):
        get_student_submission_folder_show_usecase().execute(
            student_id=student_id,
        )

    @pyqtSlot(StudentID)
    def __w_student_table_mark_result_cell_double_clicked(self, student_id: StudentID):
        dialog = MarkDialog(self)
        dialog.set_data(dialog.states.create_state_by_student_id(student_id))
        dialog.exec_()

    def __tool_bar_triggered(self, name):
        # TODO: 実行中はタスクバーのボタンを押せないようにする
        if name == "run":
            enqueue_student_tasks_if_not_run(
                parent=self,
                task_cls=RunStagesStudentTask,
            )
        elif name == "stop":
            get_task_manager().terminate()
        elif name == "clear":
            enqueue_student_tasks_if_not_run(
                parent=self,
                task_cls=CleanAllStagesStudentTask,
            )
        elif name == "settings":
            dialog = GlobalConfigEditDialog()
            dialog.exec_()
        elif name == "edit-testcases":
            # noinspection PyTypeChecker
            dialog = TestCaseListEditDialog(self)
            dialog.exec_()
        elif name == "mark":
            dialog = MarkDialog(self)
            dialog.set_data(dialog.states.create_state_of_first_student())
            dialog.exec_()
        elif name == "export-scores":
            dialog = ScoreExportDialog(self)
            dialog.exec_()
        else:
            assert False, name

    # noinspection PyPep8Naming
    def showEvent(self, event):
        # self.__task_bar_triggered("edit-testcases")
        # self.__task_bar_triggered("mark")
        pass

    def closeEvent(self, evt, **kwargs):
        # state.data_manager.save_if_necessary()
        get_task_manager().terminate()
        pass

    def __status_info_update_timer_timeout(self):
        task_manager = get_task_manager()
        io_count = psutil.Process().io_counters()
        cpu_percent = psutil.cpu_percent()
        ram_percent = psutil.virtual_memory().percent
        ram_mega_bytes = psutil.Process().memory_info().rss // 1e+6
        # noinspection PyUnresolvedReferences
        status_bar: QStatusBar = self.statusBar()
        status_bar.showMessage(
            f"タスク：{task_manager.get_running_task_count()}/{task_manager.get_task_count()} "
            # f"I/O read: {io_count.read_bytes // 1000:,}KB "
            # f"I/O write: {io_count.write_bytes // 1000:,}KB "
            # f"I/O read: {io_count.read_time}ms "
            # f"I/O write: {io_count.write_time}ms "
            f"I/O read: {io_count.read_count} "
            f"I/O write: {io_count.write_count} "
            f"CPU usage: {int(cpu_percent)}% "
            f"RAM usage: {int(ram_mega_bytes):,.0f}MB "
            # f"開発者ツール：{settings_compiler.get_vs_dev_cmd_bat_path()}"
        )
        if task_manager.get_task_count() != 0:
            # noinspection PyUnresolvedReferences
            status_bar.setStyleSheet("background-color: yellow")
        else:
            # noinspection PyUnresolvedReferences
            status_bar.setStyleSheet("")
