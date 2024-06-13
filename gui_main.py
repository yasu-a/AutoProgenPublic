from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import state
from gui_compiler_wizard import CompilerConfigurationWizard
from gui_mark import StudentMarkDialog
from gui_student import StudentInfoWidget
from gui_testcase_list import TestCaseListEditDialog
from icons import icon
from settings import settings_compiler


class ToolBar(QToolBar):
    triggered = pyqtSignal(str)  # type: ignore

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self.__init_ui()

    def __init_ui(self):
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.setIconSize(QSize(25, 25))

        a = QAction(icon("play"), "実行", self)
        a.setObjectName("run")
        self.addAction(a)

        a = QAction(icon("vs"), "コンパイラの設定", self)
        a.setObjectName("configure-compiler")
        self.addAction(a)

        a = QAction(icon("testing"), "テストケースの編集", self)
        a.setObjectName("edit-testcases")
        self.addAction(a)

        a = QAction(icon("mark"), "採点", self)
        a.setObjectName("mark")
        self.addAction(a)

        self.actionTriggered.connect(self.__triggered)  # type: ignore

    def __triggered(self, a):
        self.triggered.emit(a.objectName())


class MainWindow(QMainWindow):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self.__init_ui()
        self.__init_signals()

        timer = QTimer(self)
        timer.setInterval(100)
        timer.timeout.connect(self.__status_info_update_timer_timeout)  # type: ignore
        timer.start()  # type: ignore
        self.__context_info_update_timer = timer

    def __init_ui(self):
        self.setWindowTitle("Auto Progen")
        self.setWindowIcon(icon("title"))
        self.resize(1500, 800)

        self._tool_bar = ToolBar(self)  # type: ignore
        self.addToolBar(self._tool_bar)

        self._w_student_env = StudentInfoWidget(self)  # type: ignore
        self.setCentralWidget(self._w_student_env)

    def __init_signals(self):
        self._tool_bar.triggered.connect(self.__task_bar_triggered)

    def __task_bar_triggered(self, name):
        if name == "run":
            state.project_service.clear_all_test_results()
            state.task_dispatcher.run_full_process_for_all_students()
        elif name == "configure-compiler":
            wizard = CompilerConfigurationWizard(self)
            if wizard.exec_() == QDialog.Accepted:
                settings_compiler.set_vs_dev_cmd_bat_path(wizard.result_path())
                settings_compiler.commit()
        elif name == "edit-testcases":
            # noinspection PyTypeChecker
            dialog = TestCaseListEditDialog(self)
            dialog.exec_()
        elif name == "mark":
            # noinspection PyTypeChecker
            dialog = StudentMarkDialog(self)
            dialog.exec_()
        else:
            assert False, name

    def showEvent(self, event):
        # self.__task_bar_triggered("edit-testcases")
        # self.__task_bar_triggered("mark")
        pass

    def closeEvent(self, evt, **kwargs):
        state.data_manager.save_if_necessary()

    def __status_info_update_timer_timeout(self):
        self.statusBar().showMessage(
            f"タスク：{state.tasks.count_running_tasks()}/{state.tasks.count_tasks_in_queue()} "
            f"開発者ツール：{settings_compiler.get_vs_dev_cmd_bat_path()}"
        )
        if state.tasks.count_running_tasks() != 0:
            self.statusBar().setStyleSheet("background-color: yellow")
        else:
            self.statusBar().setStyleSheet("")
