from typing import Callable

from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QMessageBox, QWidget

from application.container import AppContainer, ProjectContainer
from control.dialog_progress import AbstractProgressDialog
from control.interface_navigator import INavigator
from domain.model.value import ProjectID, StudentID


class Navigator(INavigator):
    # アプリ起動・トップレベル遷移を扱う最小Navigator

    def __init__(self, *, app_container: AppContainer):
        self._app_container = app_container
        self._current_window: QMainWindow | None = None
        self._current_project_container: ProjectContainer | None = None
        self._handling_workspace_close = False

    def start(self) -> bool:
        return self.transition_to_launcher()

    def transition_from_launcher_to_workspace(self, project_id: ProjectID) -> QMainWindow:
        self._open_project_and_prepare_container(project_id)
        return self._show_main_window()

    def transition_from_workspace_to_launcher(self, current_window: QMainWindow) -> None:
        if self._handling_workspace_close:
            return

        self._handling_workspace_close = True
        try:
            # closeEvent側でwindowは既にclose済みなので、Navigatorは参照だけ外す
            if self._current_window is current_window:
                self._current_window = None
            self._perform_stop_tasks_if_needed(current_window)
            self._current_project_container = None
        finally:
            self._handling_workspace_close = False

        if not self.transition_to_launcher():
            QApplication.quit()

    def transition_to_launcher(self) -> bool:
        return self._show_welcome_dialog()

    def open_setting_dialog(self, parent: QWidget) -> None:
        from control.dialog_global_settings import GlobalSettingsEditDialog
        assert self._current_project_container is not None
        dialog = GlobalSettingsEditDialog(
            parent,
            compiler_search_usecase=self._app_container.compiler_search_usecase,
            test_compile_stage_usecase=self._current_project_container.test_compile_stage_usecase,
            global_settings_get_usecase=self._app_container.global_settings_get_usecase,
            global_settings_put_usecase=self._app_container.global_settings_put_usecase,
        )
        dialog.exec_()

    def open_about_dialog(self, parent: QWidget) -> None:
        from control.dialog_about import AboutDialog
        dialog = AboutDialog(parent)
        dialog.exec_()

    def open_score_export_dialog(self, parent: QWidget) -> None:
        from control.dialog_score_export import ScoreExportDialog
        assert self._current_project_container is not None
        dialog = ScoreExportDialog(
            parent,
            global_settings_get_usecase=self._app_container.global_settings_get_usecase,
            score_excel_list_worksheet_stats_usecase=self._app_container.score_excel_list_worksheet_stats_usecase,
            score_excel_has_data_usecase=self._app_container.score_excel_has_data_usecase,
            score_excel_apply_usecase=self._app_container.score_excel_apply_usecase,
            student_list_id_usecase=self._current_project_container.student_list_id_usecase,
            student_mark_list_usecase=self._current_project_container.student_mark_list_usecase,
            target_id=self._current_project_container.current_project_repository.get().target_id,
        )
        dialog.exec_()

    def open_scoring_dialog(self, parent: QWidget) -> None:
        from control.dialog_mark import MarkDialog
        assert self._current_project_container is not None
        dialog = MarkDialog(
            parent,
            global_settings_get_usecase=self._app_container.global_settings_get_usecase,
            student_list_id_usecase=self._current_project_container.student_list_id_usecase,
            testcase_config_list_id_usecase=self._current_project_container.testcase_config_list_id_usecase,
            student_mark_view_data_get_mark_summary_usecase=self._current_project_container.student_mark_view_data_get_mark_summary_usecase,
            student_mark_view_data_get_test_result_usecase=self._current_project_container.student_mark_view_data_get_test_result_usecase,
            student_source_code_get_usecase=self._current_project_container.student_source_code_get_usecase,
            student_mark_get_usecase=self._current_project_container.student_mark_get_usecase,
            student_mark_put_usecase=self._current_project_container.student_mark_put_usecase,
        )
        dialog.set_state(dialog.states.create_state_of_first_student())
        dialog.exec_()

    def open_scoring_dialog_for_student(self, parent: QWidget, student_id: StudentID) -> None:
        from control.dialog_mark import MarkDialog
        assert self._current_project_container is not None
        dialog = MarkDialog(
            parent,
            global_settings_get_usecase=self._app_container.global_settings_get_usecase,
            student_list_id_usecase=self._current_project_container.student_list_id_usecase,
            testcase_config_list_id_usecase=self._current_project_container.testcase_config_list_id_usecase,
            student_mark_view_data_get_mark_summary_usecase=self._current_project_container.student_mark_view_data_get_mark_summary_usecase,
            student_mark_view_data_get_test_result_usecase=self._current_project_container.student_mark_view_data_get_test_result_usecase,
            student_source_code_get_usecase=self._current_project_container.student_source_code_get_usecase,
            student_mark_get_usecase=self._current_project_container.student_mark_get_usecase,
            student_mark_put_usecase=self._current_project_container.student_mark_put_usecase,
        )
        dialog.set_state(dialog.states.create_state_by_student_id(student_id))
        dialog.exec_()

    def open_testcase_list_edit_dialog(self, parent: QWidget) -> None:
        from control.dialog_testcase_list_edit import TestCaseListEditDialog
        assert self._current_project_container is not None
        dialog = TestCaseListEditDialog(
            parent,
            global_settings_get_usecase=self._app_container.global_settings_get_usecase,
            test_test_stage_usecase=self._app_container.test_test_stage_usecase,
            testcase_list_summary_usecase=self._current_project_container.testcase_list_summary_usecase,
            testcase_create_new_name_usecase=self._current_project_container.testcase_create_new_name_usecase,
            testcase_create_usecase=self._current_project_container.testcase_create_usecase,
            testcase_copy_usecase=self._current_project_container.testcase_copy_usecase,
            testcase_delete_usecase=self._current_project_container.testcase_delete_usecase,
            testcase_get_usecase=self._current_project_container.testcase_get_usecase,
            testcase_put_usecase=self._current_project_container.testcase_put_usecase,
        )
        dialog.exec_()

    def _launch_new_project(self, new_project_config) -> QMainWindow | None:
        project_id = self._app_container.project_create_usecase.execute(
            project_name=new_project_config.project_name,
            target_number=new_project_config.target_number,
            zip_name=new_project_config.manaba_report_archive_fullpath.name,
        )
        self._open_project_and_prepare_container(project_id)

        result = AbstractProgressDialog.run_blocking_task(
            parent=None,  # type: ignore[arg-type]
            title="プロジェクトの初期化",
            initial_message="初期化を開始しています...",
            task_func=self._current_project_container.create_current_project_initialize_static_usecase(
                manaba_report_archive_fullpath=new_project_config.manaba_report_archive_fullpath,
            ).execute,
        )
        if result is not None and result.has_error:
            QMessageBox.critical(
                None,
                "プロジェクトの初期化",
                result.message,
                QMessageBox.Ok,
            )
            return None

        return self._show_main_window()

    @staticmethod
    def _open_project(project_id: ProjectID, app_container: AppContainer) -> None:
        app_container.project_open_usecase.execute(project_id)

    def _open_project_and_prepare_container(self, project_id: ProjectID) -> None:
        self._open_project(project_id, self._app_container)
        self._current_project_container = self._app_container.create_project_container(project_id)

    def _show_main_window(self) -> QMainWindow:
        from control.window_main import MainWindow

        assert self._current_project_container is not None
        return self._replace_main_window(
            lambda: MainWindow(
                navigator=self,
                app_container=self._app_container,
                project_container=self._current_project_container,
            )
        )

    def _show_welcome_dialog(self) -> bool:
        from control.dialog_welcome import WelcomeDialog
        from control.dto.new_project_config import NewProjectConfig

        welcome = WelcomeDialog(app_container=self._app_container)
        if welcome.exec_() != QDialog.Accepted:
            return False

        result = welcome.get_data()
        if isinstance(result, ProjectID):
            self.transition_from_launcher_to_workspace(result)
            return True
        if isinstance(result, NewProjectConfig):
            return self._launch_new_project(result) is not None

        assert False, result

    def _replace_main_window(self, factory_func: Callable[[], QMainWindow]) -> QMainWindow:
        old_window = self._current_window
        if old_window is not None:
            old_window.deleteLater()

        new_window = factory_func()
        self._current_window = new_window
        new_window.show()
        return new_window

    def _perform_stop_tasks_if_needed(self, parent: QWidget) -> None:
        if self._current_project_container is None:
            return
        task_manager = self._current_project_container.task_manager
        if task_manager.is_empty():
            return
        AbstractProgressDialog.run_blocking_task(
            parent=parent,
            title="タスクの停止",
            initial_message="停止処理を開始します...",
            task_func=task_manager.terminate,
        )
