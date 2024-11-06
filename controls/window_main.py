from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from application.dependency.tasks import get_task_manager
from application.dependency.usecases import get_current_project_summary_get_usecase, \
    get_student_list_id_usecase, get_student_submission_folder_show_usecase, \
    get_resource_usage_get_usecase
from controls.dialog_global_config import GlobalConfigEditDialog
from controls.dialog_mark import MarkDialog
from controls.dialog_score_export import ScoreExportDialog
from controls.dialog_stop_tasks import StopTasksDialog
from controls.dialog_testcase_list_edit import TestCaseListEditDialog
from controls.res.fonts import get_font
from controls.tasks.clean_all_stages import CleanAllStagesStudentTask
from controls.tasks.run_stages import RunStagesStudentTask
from controls.widget_student_table import StudentTableWidget
from controls.widget_toolbar import ToolBar
from domain.models.values import StudentID
from infra.tasks.task import AbstractStudentTask
from usecases.dto.resource_usage import ResourceUsageGetResult
from utils.app_logging import create_logger


class ProcessResourceUsageStatusBarWidget(QWidget):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._timer = QTimer(self)
        self._timer.setInterval(1000)

        self._init_ui()
        self._init_signals()

        self._timer.start()

    def _init_ui(self):
        self.setStyleSheet(
            "QLabel {"
            "   color: black;"
            "   background-color: #ffffff;"
            "   border-radius: 4px;"
            "   padding: 2px;"
            "}"
        )

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self._l_disk_read_count = QLabel(self)
        layout.addWidget(self._l_disk_read_count)

        self._l_disk_write_count = QLabel(self)
        layout.addWidget(self._l_disk_write_count)

        self._l_cpu_percent = QLabel(self)
        layout.addWidget(self._l_cpu_percent)

        self._l_memory = QLabel(self)
        layout.addWidget(self._l_memory)

    def _init_signals(self):
        # noinspection PyUnresolvedReferences
        self._timer.timeout.connect(self.__timer_timeout)

    @pyqtSlot()
    def __timer_timeout(self):
        result: ResourceUsageGetResult = get_resource_usage_get_usecase().execute()
        self._l_cpu_percent.setText(f"CPU: {result.cpu_percent}%")
        self._l_memory.setText(f"RAM: {result.memory_mega_bytes:,} MB")
        self._l_disk_read_count.setText(f"Disk read: {result.disk_read_count:,}")
        self._l_disk_write_count.setText(f"Disk write: {result.disk_write_count:,}")


class TaskStateStatusBarWidget(QWidget):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self.__icon_anim_state = 0

        self._icon_timer = QTimer(self)
        self._icon_timer.setInterval(100)

        self._update_timer = QTimer(self)
        self._update_timer.setInterval(1000)

        self._init_ui()
        self._init_signals()

        self._icon_timer.start()
        self._update_timer.start()

    def _init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self._l_icon = QLabel(self)
        self._l_icon.setFont(get_font(monospace=True))
        layout.addWidget(self._l_icon)

        self._l_message = QLabel(self)
        self._l_message.setEnabled(False)
        layout.addWidget(self._l_message)

    def _init_signals(self):
        self._icon_timer.timeout.connect(self.__icon_timer_timeout)
        self._update_timer.timeout.connect(self.__update_timer_timeout)

    @pyqtSlot()
    def __icon_timer_timeout(self):
        task_manager = get_task_manager()
        if task_manager.is_empty():
            self._l_icon.setText("")
        else:
            self._l_icon.setText((">" * self.__icon_anim_state).ljust(10, "."))
            self.__icon_anim_state = (self.__icon_anim_state + 1) % 11

    @pyqtSlot()
    def __update_timer_timeout(self):
        task_manager = get_task_manager()
        if task_manager.is_empty():
            self._l_message.setText(
                "実行中のタスクはありません"
            )
            color = "black"
            background_color = "none"
        else:
            self._l_message.setText(
                f"実行中のタスク: {task_manager.count_active()}/{task_manager.count()}"
            )
            color = "white"
            background_color = "#cc3300"
        self.setStyleSheet(
            "QLabel {"
            f"  color: {color};"
            f"  background-color: {background_color};"
            "   border-radius: 4px;"
            "   padding: 2px;"
            "}"
        )


class MainWindow(QMainWindow):
    _logger = create_logger()

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        project_summary = get_current_project_summary_get_usecase().execute()

        self.setWindowTitle(
            f"{project_summary.project_name} 設問{project_summary.target_number}"
        )
        self.resize(1500, 800)

        # ツールバー
        self._tool_bar = ToolBar(self)
        self.addToolBar(self._tool_bar)

        # 生徒のテーブル
        self._w_student_table = StudentTableWidget(self)
        self.setCentralWidget(self._w_student_table)

        # ステータスバー
        self._sb_task_state = TaskStateStatusBarWidget(self)
        self.statusBar().addPermanentWidget(self._sb_task_state)
        self.statusBar().addPermanentWidget(QLabel(self), 1)
        self._sb_process_resource_usage = ProcessResourceUsageStatusBarWidget(self)
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
        get_student_submission_folder_show_usecase().execute(
            student_id=student_id,
        )

    @pyqtSlot(StudentID)
    def __w_student_table_mark_result_cell_triggered(self, student_id: StudentID):
        dialog = MarkDialog(self)
        dialog.set_data(dialog.states.create_state_by_student_id(student_id))
        dialog.exec_()

    @classmethod
    def __perform_stop_tasks(cls):
        if get_task_manager().count():
            dialog = StopTasksDialog()
            dialog.exec_()

    @classmethod
    def __enqueue_student_tasks_if_not_run(cls, parent, task_cls: type[AbstractStudentTask]):
        if get_task_manager().count() > 0:
            return
        for student_id in get_student_list_id_usecase().execute():
            get_task_manager().enqueue(
                task_cls(
                    parent=parent,
                    student_id=student_id,
                )
            )

    def __tool_bar_triggered(self, name):
        self._tool_bar.update_button_state(is_task_alive=True)
        if name == "run":
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
            dialog = GlobalConfigEditDialog()
            dialog.exec_()
        elif name == "edit-testcases":
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

    def closeEvent(self, evt, **kwargs):
        self.__perform_stop_tasks()
        pass
