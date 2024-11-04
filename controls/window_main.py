import psutil
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from app_logging import create_logger
from application.dependency.tasks import get_task_manager
from application.dependency.usecases import get_current_project_summary_get_usecase, \
    get_student_list_id_usecase, get_student_submission_folder_show_usecase
from controls.dialog_global_settings import GlobalSettingsEditDialog
from controls.dialog_mark import MarkDialog
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
            dialog = GlobalSettingsEditDialog()
            dialog.exec_()
        elif name == "edit-testcases":
            # noinspection PyTypeChecker
            dialog = TestCaseListEditDialog(self)
            dialog.exec_()
        elif name == "mark":
            dialog = MarkDialog(self)
            dialog.set_data(dialog.states.create_state_of_first_student())
            dialog.exec_()
        else:
            assert False, name
        # if name == "run":
        #     state.project_service.clear_all_test_results()
        #     state.task_dispatcher.run_full_process_for_all_students()
        # elif name == "configure-compiler":
        #     wizard = CompilerConfigurationWizard(self)
        #     if wizard.exec_() == QDialog.Accepted:
        #         settings_compiler.set_vs_dev_cmd_bat_path(wizard.result_path())
        #         settings_compiler.commit()
        # elif name == "edit-testcases":
        #     # noinspection PyTypeChecker
        #     dialog = TestCaseListEditDialog(self)
        #     dialog.exec_()
        # elif name == "mark":
        #     # noinspection PyTypeChecker
        #     dialog = StudentMarkDialog(self)
        #     dialog.exec_()
        # elif name == "export-scores":
        #     with state.data(readonly=True) as data:
        #         student_ids = data.student_ids
        #     exporter = ScoreExporter(student_ids=student_ids)
        #
        #     # noinspection PyTypeChecker
        #     excel_path = QFileDialog.getOpenFileName(
        #         self,
        #         "点数をエクスポートするエクセルファイルの選択",
        #     )[0]
        #     if not excel_path or not os.path.exists(excel_path):
        #         QMessageBox().critical(
        #             self,
        #             "点数のエクスポート",
        #             "正しいエクセルファイルが選択されませんでした",
        #         )
        #         return
        #     exporter.set_excel_path(excel_path)
        #
        #     ws_names = exporter.list_valid_worksheet_names()
        #     if not ws_names:
        #         QMessageBox().critical(
        #             self,
        #             "点数のエクスポート",
        #             "エクスポート先のワークシートが１つも見つかりません",
        #         )
        #         return
        #
        #     # noinspection PyTypeChecker
        #     ws_name, ok = QInputDialog.getItem(
        #         self,
        #         "点数のエクスポート",
        #         "エクスポート先のワークシートを選択してください",
        #         exporter.list_valid_worksheet_names(),
        #         0,
        #         False,
        #     )
        #     if not ok:
        #         return
        #     exporter.set_worksheet_name(ws_name)
        #
        #     # noinspection PyTypeChecker
        #     target_number, ok = QInputDialog.getItem(
        #         self,
        #         "点数のエクスポート",
        #         "エクスポートする設問番号を選択してください",
        #         [
        #             f"設問 {target_number:02}"
        #             for target_number in state.project_service.list_registered_target_numbers()
        #         ],
        #         0,
        #         False,
        #     )
        #     if not ok:
        #         return
        #     target_number = int(re.findall(r"\d+", target_number)[0])
        #     assert target_number in state.project_service.list_registered_target_numbers()
        #     exporter.set_target_number(target_number)
        #
        #     scores = {}
        #     with state.data(readonly=True) as data:
        #         for student in data.students.values():
        #             student_id = student.meta.student_id
        #             score = student.mark_scores.get(target_number, -1)
        #             scores[student_id] = score
        #     exporter.set_scores(scores)
        #
        #     try:
        #         if exporter.has_data():
        #             # noinspection PyTypeChecker
        #             if QMessageBox.question(
        #                     self,
        #                     "点数のエクスポート",
        #                     f"シート名{ws_name}の設問{target_number}に入力データが存在しますが上書きしてよろしいですか？",
        #                     QMessageBox.Yes | QMessageBox.No,
        #                     QMessageBox.No,
        #             ) == QMessageBox.No:
        #                 QMessageBox().critical(
        #                     self,
        #                     "点数のエクスポート",
        #                     "エクスポートを中断しました",
        #                 )
        #                 return
        #         exporter.commit()
        #     except Exception as e:
        #         self._logger.info("Failed to commit scores to the workbook")
        #         self._logger.exception(e)
        #         # noinspection PyTypeChecker
        #         QMessageBox.critical(
        #             self,
        #             "点数のエクスポート",
        #             "エクスポートに失敗しました。\n" + "\n".join(map(str, e.args)),
        #         )
        #     else:
        #         # noinspection PyTypeChecker
        #         QMessageBox.information(
        #             self,
        #             "点数のエクスポート",
        #             "元のファイルをバックアップしてエクスポートしました。ワークブックを開いて確認してください。"
        #         )
        #         os.startfile(os.path.dirname(excel_path))
        # else:
        #     assert False, name
        pass

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
