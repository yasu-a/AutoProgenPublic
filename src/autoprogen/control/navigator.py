from typing import TYPE_CHECKING, Callable

from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QMessageBox, QWidget

from autoprogen.application.container import AppContainer, ProjectContainer
from autoprogen.control.dialog_progress import AbstractProgressDialog
from autoprogen.control.interface_navigator import INavigator
from autoprogen.domain.error.stage.compile import SourceSafetyViolationError
from autoprogen.domain.model.project_settings import SourceCodeCheckSkip
from autoprogen.domain.model.source_code import SourceCode
from autoprogen.domain.model.value import ProjectID, StudentID
from autoprogen.util.app_logging import create_logger

if TYPE_CHECKING:
    from autoprogen.control.widget_source_safety_error import SourceSafetyErrorWidget


class Navigator(INavigator):
    """アプリ起動とトップレベル画面間の遷移を管理する。"""

    _logger = create_logger()

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
        from autoprogen.control.dialog_global_settings import GlobalSettingsEditDialog
        assert self._current_project_container is not None
        dialog = GlobalSettingsEditDialog(
            parent,
            compiler_search_usecase=self._app_container.compiler_search_usecase,
            test_compile_stage_usecase=self._current_project_container.test_compile_stage_usecase,
            global_settings_get_usecase=self._app_container.global_settings_get_usecase,
            global_settings_put_usecase=self._app_container.global_settings_put_usecase,
        )
        dialog.exec_()

    def open_project_settings_dialog(self, parent: QWidget) -> None:
        """現在のプロジェクト専用の静的チェック設定を編集する。"""
        from autoprogen.control.dialog_project_settings import ProjectSettingsEditDialog
        assert self._current_project_container is not None
        container = self._current_project_container
        dialog = ProjectSettingsEditDialog(
            parent,
            catalog=container.source_code_check_catalog_factory.create(),
            project_settings_get_usecase=container.project_settings_get_usecase,
            project_settings_put_usecase=container.project_settings_put_usecase,
        )
        dialog.exec_()

    def open_student_error_detail_dialog(self, parent: QWidget, student_id: StudentID) -> None:
        """学生のエラー詳細を取得し、編集不可のダイアログに表示する。"""
        from autoprogen.control.dialog_student_error_detail import StudentErrorDetailDialog
        assert self._current_project_container is not None
        container = self._current_project_container
        row = container.student_table_load_usecase.execute_row(student_id)
        if not row.error_cell.text_entries:
            return
        dialog = StudentErrorDetailDialog(
            parent,
            student_id=student_id,
            error_entries=row.error_cell.text_entries,
        )
        # 構造化エラーから安全性チェック停止だけを専用表示の対象にする。
        safety_errors = tuple(
            entry.error
            for entry in row.error_cell.text_entries
            if isinstance(entry.error, SourceSafetyViolationError)
        )
        if safety_errors:
            from autoprogen.control.widget_source_safety_error import SourceSafetyErrorWidget
            try:
                source_code = container.student_source_code_get_usecase.execute(student_id)
            except UnicodeError:
                source_code = None
            global_settings = self._app_container.global_settings_get_usecase.execute()
            project_settings = container.project_settings_get_usecase.execute()
            source_hashes = {error.source_sha256 for error in safety_errors}
            source_sha256 = (
                next(iter(source_hashes)) if len(source_hashes) == 1 else None
            )
            already_approved = (
                source_sha256 is not None
                and SourceCodeCheckSkip(student_id, source_sha256)
                in project_settings.source_code_check_skips
            )
            widget = SourceSafetyErrorWidget(
                dialog,
                source_code=source_code,
                safety_errors=safety_errors,
                show_editing_symbols=global_settings.show_editing_symbols_in_source_code,
                enable_line_wrap=global_settings.enable_line_wrap_in_source_code,
                can_approve=container.task_manager.is_empty(),
                already_approved=already_approved,
            )
            widget.approval_requested.connect(
                lambda: self._approve_source_code_check_skip(
                    parent=widget,
                    widget=widget,
                    student_id=student_id,
                    displayed_source_code=source_code,
                    expected_sha256=source_sha256,
                )
            )
            dialog.set_extension_widget(widget)
        dialog.exec_()

    def _approve_source_code_check_skip(
        self,
        *,
        parent: QWidget,
        widget: "SourceSafetyErrorWidget",
        student_id: StudentID,
        displayed_source_code: SourceCode | None,
        expected_sha256: str | None,
    ) -> None:
        """表示したソースの同一性を確認し、安全性チェックの省略を保存する。"""
        assert self._current_project_container is not None
        if displayed_source_code is None or expected_sha256 is None:
            return
        container = self._current_project_container
        try:
            # 確認前に保存済みソースが表示内容と一致しているか検証する。
            current_source_code = container.student_source_code_get_usecase.execute(student_id)
            if (
                    current_source_code != displayed_source_code
                    or current_source_code.calculate_sha256() != expected_sha256
            ):
                widget.set_approval_state(
                    "ソースコードが更新されました。再実行してから許可してください。",
                    enabled=False,
                )
                return

            # 採点者へ省略対象が現在の学生とソースだけであることを確認する。
            decision = QMessageBox.question(
                parent,
                "安全性チェックの許可",
                "この学生の現在のソースコードだけを許可しますか？\n"
                "次回実行時に安全性チェックを省略します。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if decision != QMessageBox.Yes:
                return

            # 確認中にソースが変更されていないか保存直前に再検証する。
            current_source_code = container.student_source_code_get_usecase.execute(student_id)
            if (
                    current_source_code != displayed_source_code
                    or current_source_code.calculate_sha256() != expected_sha256
            ):
                widget.set_approval_state(
                    "ソースコードが更新されました。再実行してから許可してください。",
                    enabled=False,
                )
                return

            # 現在のプロジェクト設定へ学生とソースの組み合わせを追加する。
            settings = container.project_settings_get_usecase.execute()
            updated = settings.with_source_code_check_skip(
                student_id=student_id,
                source_sha256=expected_sha256,
            )
            if updated != settings:
                container.project_settings_put_usecase.execute(updated)
        except Exception as error:
            self._logger.exception("ソースコードの許可を保存できませんでした")
            QMessageBox.critical(
                parent,
                "安全性チェックの許可",
                f"設定を保存できませんでした。\n{error}",
            )
            return

        # 保存完了を表示し、同じ許可操作を繰り返せないようにする。
        widget.set_approval_state(
            "許可を保存しました。次に「実行」を押すとCOMPILEを再試行します。",
            enabled=False,
        )

    def open_about_dialog(self, parent: QWidget) -> None:
        from autoprogen.control.dialog_about import AboutDialog
        dialog = AboutDialog(parent)
        dialog.exec_()

    def open_score_export_dialog(self, parent: QWidget) -> None:
        from autoprogen.control.dialog_score_export import ScoreExportDialog
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
        from autoprogen.control.dialog_mark import MarkDialog
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
        from autoprogen.control.dialog_mark import MarkDialog
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

    def open_testcase_list_edit_dialog(self, parent: QWidget) -> bool:
        """テストケース編集画面を開き、変更の有無を呼び出し元へ返す。"""
        from autoprogen.control.dialog_testcase_list_edit import TestCaseListEditDialog
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
        return dialog.has_changes

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
            task_func=self._current_project_container.current_project_initialize_static_usecase.execute,
            manaba_report_archive_fullpath=new_project_config.manaba_report_archive_fullpath,
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
        from autoprogen.control.window_main import MainWindow

        assert self._current_project_container is not None
        return self._replace_main_window(
            lambda: MainWindow(
                navigator=self,
                app_container=self._app_container,
                project_container=self._current_project_container,
            )
        )

    def _show_welcome_dialog(self) -> bool:
        """ランチャー画面を表示し、利用者が選択した処理へ遷移する。"""
        from autoprogen.control.dialog_welcome import WelcomeDialog
        from autoprogen.control.dto.new_project_config import NewProjectConfig

        welcome = WelcomeDialog(
            auto_generate_project_name=(
                self._app_container.debug_settings.auto_generate_project_name
            ),
            initial_report_archive_fullpath=(
                self._app_container.debug_settings.report_archive_fullpath
            ),
            initial_target_number=self._app_container.debug_settings.target_number,
            project_check_exist_by_name_usecase=self._app_container.project_check_exist_by_name_usecase,
            manaba_report_archive_validate_master_excel_exists_usecase=(
                self._app_container.manaba_report_archive_validate_master_excel_exists_usecase
            ),
            project_list_recent_summary_usecase=self._app_container.project_list_recent_summary_usecase,
            project_folder_show_usecase=self._app_container.project_folder_show_usecase,
            project_delete_usecase=self._app_container.project_delete_usecase,
            project_base_folder_show_usecase=self._app_container.project_base_folder_show_usecase,
            project_get_size_query_usecase=self._app_container.project_get_size_query_usecase,
        )
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
