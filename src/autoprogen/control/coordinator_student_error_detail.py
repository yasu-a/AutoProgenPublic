from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QVBoxLayout, QWidget

from autoprogen.control.interface_navigator import INavigator
from autoprogen.control.widget_not_submitted_error import NotSubmittedErrorWidget
from autoprogen.control.widget_error_navigation import (
    GlobalSettingsNavigationWidget,
    TestcaseListNavigationWidget,
)
from autoprogen.control.widget_source_safety_error import SourceSafetyErrorWidget
from autoprogen.control.widget_submission_file_recovery import (
    SubmissionFileRecoveryWidget,
)
from autoprogen.control.widget_student_error_detail import StudentErrorDetailWidget
from autoprogen.domain.error.stage.build import (
    MultipleSourceFilesError,
    SourceEncodingUnknownError,
    SourceFilenameMultipleNumbersError,
    SourceFilenameNoNumberError,
    SubmissionNotFoundError,
    SubmissionSourceNotFoundError,
)
from autoprogen.domain.error.stage.compile import (
    CompilerNotConfiguredError,
    CompilerTimeoutError,
    SourceSafetyViolationError,
    VsDevToolNotFoundError,
)
from autoprogen.domain.error.stage.execute import ExecutionTimeoutError
from autoprogen.domain.error.stage.test import OutputMatchingError
from autoprogen.domain.model.project_settings import SourceCodeCheckSkip
from autoprogen.domain.model.value import StudentID
from autoprogen.infra.task.manager import TaskManager
from autoprogen.usecase.global_settings import GlobalSettingsGetUseCase
from autoprogen.usecase.main_window import MainWindowFacade
from autoprogen.usecase.project_settings import (
    BuildErrorStudentExcludeUseCase,
    BuildErrorStudentExcludeUseCaseError,
    ProjectSettingsGetUseCase,
)
from autoprogen.usecase.source_code_check_skip import (
    SourceCodeCheckSkipApproveUseCase,
    SourceCodeCheckSkipApproveUseCaseError,
)
from autoprogen.usecase.student_mark import StudentMarkGetUseCase
from autoprogen.usecase.student_source_code import StudentSourceCodeGetUseCase
from autoprogen.util.app_logging import create_logger


class StudentErrorDetailCoordinator(QObject):
    """学生のエラー詳細Widgetを構成し、処置要求とUseCaseを仲介する。"""

    _logger = create_logger()
    testcase_list_changed = pyqtSignal(name="testcase_list_changed")

    def __init__(
            self,
            *,
            navigator: INavigator,
            main_window_facade: MainWindowFacade,
            student_source_code_get_usecase: StudentSourceCodeGetUseCase,
            global_settings_get_usecase: GlobalSettingsGetUseCase,
            project_settings_get_usecase: ProjectSettingsGetUseCase,
            source_code_check_skip_approve_usecase: SourceCodeCheckSkipApproveUseCase,
            build_error_student_exclude_usecase: BuildErrorStudentExcludeUseCase,
            student_mark_get_usecase: StudentMarkGetUseCase,
            task_manager: TaskManager,
    ) -> None:
        """表示情報の取得経路とエラー固有の処置UseCaseを受け取る。"""
        super().__init__()
        self._navigator = navigator
        self._main_window_facade = main_window_facade
        self._student_source_code_get_usecase \
            = student_source_code_get_usecase
        self._global_settings_get_usecase \
            = global_settings_get_usecase
        self._project_settings_get_usecase \
            = project_settings_get_usecase
        self._source_code_check_skip_approve_usecase \
            = source_code_check_skip_approve_usecase
        self._build_error_student_exclude_usecase \
            = build_error_student_exclude_usecase
        self._student_mark_get_usecase \
            = student_mark_get_usecase
        self._task_manager = task_manager

    def create_widget(
            self,
            parent: QWidget,
            student_id: StudentID,
    ) -> QWidget | None:
        """最新の学生エラーからDock用のWidgetを生成する。"""
        row = self._main_window_facade.load_student_table_row(student_id)
        if not row.error_cell.text_entries:
            return None

        # 共有ステージの同一エラーが複数パスに保存されていても一度だけ表示する。
        error_entries = row.error_cell.distinct_text_entries()
        detail_widget = StudentErrorDetailWidget(
            parent,
            error_entries=error_entries,
        )
        extension_widgets: list[QWidget] = []

        safety_errors = tuple(
            entry.error
            for entry in error_entries
            if isinstance(entry.error, SourceSafetyViolationError)
        )
        if safety_errors:
            extension_widgets.append(self._create_source_safety_widget(
                parent=detail_widget,
                student_id=student_id,
                safety_errors=safety_errors,
            ))

        if any(
                isinstance(entry.error, SubmissionNotFoundError)
                for entry in error_entries
        ):
            extension_widgets.append(self._create_not_submitted_widget(
                parent=detail_widget,
                student_id=student_id,
            ))

        if any(isinstance(entry.error, (
                SourceFilenameMultipleNumbersError,
                SourceFilenameNoNumberError,
                MultipleSourceFilesError,
                SubmissionSourceNotFoundError,
                SourceEncodingUnknownError,
        )) for entry in error_entries):
            extension_widgets.append(
                self._create_submission_file_recovery_widget(
                    parent=detail_widget,
                    student_id=student_id,
                )
            )

        if any(isinstance(entry.error, (
                CompilerNotConfiguredError,
                VsDevToolNotFoundError,
                CompilerTimeoutError,
        )) for entry in error_entries):
            widget = GlobalSettingsNavigationWidget(
                parent=detail_widget,
                message=(
                    "グローバル設定の確認が必要です。\n"
                    "コンパイラのパスやコンパイル時間制限を確認してください。"
                ),
                button_text="グローバル設定を開く",
            )
            widget.global_settings_requested.connect(
                lambda parent=widget: self._open_global_settings(parent),
            )
            extension_widgets.append(widget)

        if any(isinstance(entry.error, (
                ExecutionTimeoutError,
                OutputMatchingError,
        )) for entry in error_entries):
            widget = TestcaseListNavigationWidget(
                parent=detail_widget,
                message=(
                    "テストケースの確認が必要です。\n"
                    "入力内容、実行時間制限、期待する出力を確認してください。"
                ),
                button_text="テストケース一覧を開く",
            )
            widget.testcase_list_requested.connect(
                lambda parent=widget: self._open_testcase_list(parent),
            )
            extension_widgets.append(widget)

        if len(extension_widgets) == 1:
            detail_widget.set_extension_widget(extension_widgets[0])
        elif extension_widgets:
            # 異なる処置が同時に必要な場合は、いずれも失わず縦に並べる。
            extensions = QWidget(detail_widget)
            extensions_layout = QVBoxLayout(extensions)
            extensions_layout.setContentsMargins(0, 0, 0, 0)
            for extension_widget in extension_widgets:
                extensions_layout.addWidget(extension_widget)
            detail_widget.set_extension_widget(extensions)
        return detail_widget

    def _open_global_settings(self, parent: QWidget) -> None:
        """既存Navigatorを通じてグローバル設定画面を開く。"""
        if self._task_manager.is_empty():
            self._navigator.open_setting_dialog(parent)

    def _open_testcase_list(self, parent: QWidget) -> None:
        """既存Navigatorを通じてテストケース一覧を開き、変更を通知する。"""
        if not self._task_manager.is_empty():
            return
        if self._navigator.open_testcase_list_edit_dialog(parent):
            self.testcase_list_changed.emit()

    def _create_source_safety_widget(
            self,
            *,
            parent: QWidget,
            student_id: StudentID,
            safety_errors: tuple[SourceSafetyViolationError, ...],
    ) -> SourceSafetyErrorWidget:
        """安全性チェック停止の表示Widgetを生成して許可要求を接続する。"""
        try:
            source_code = self._student_source_code_get_usecase.execute(student_id)
        except UnicodeError:
            source_code = None
        global_settings = self._global_settings_get_usecase.execute()
        project_settings = self._project_settings_get_usecase.execute()
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
            parent,
            source_code=source_code,
            safety_errors=safety_errors,
            show_editing_symbols=(
                global_settings.show_editing_symbols_in_source_code
            ),
            enable_line_wrap=global_settings.enable_line_wrap_in_source_code,
            can_approve=self._task_manager.is_empty(),
            already_approved=already_approved,
        )
        widget.approval_requested.connect(
            lambda: self._on_approval_requested(
                parent=widget,
                widget=widget,
                student_id=student_id,
                expected_sha256=source_sha256,
            )
        )
        return widget

    def _create_not_submitted_widget(
            self,
            *,
            parent: QWidget,
            student_id: StudentID,
    ) -> NotSubmittedErrorWidget:
        """未提出エラーの処置Widgetを生成して除外要求を接続する。"""
        settings = self._project_settings_get_usecase.execute()
        widget = NotSubmittedErrorWidget(
            parent,
            can_exclude=self._task_manager.is_empty(),
            already_excluded=student_id in settings.bulk_grading_skips,
        )
        widget.exclusion_requested.connect(
            lambda: self._on_exclusion_requested(
                parent=widget,
                widget=widget,
                student_id=student_id,
            )
        )
        return widget

    def _create_submission_file_recovery_widget(
            self,
            *,
            parent: QWidget,
            student_id: StudentID,
    ) -> SubmissionFileRecoveryWidget:
        """提出ファイルエラーの閲覧と0点・除外要求を接続する。"""
        settings = self._project_settings_get_usecase.execute()
        widget = SubmissionFileRecoveryWidget(
            parent,
            can_exclude=self._task_manager.is_empty(),
            already_excluded=student_id in settings.bulk_grading_skips,
        )
        widget.submission_view_requested.connect(
            lambda: self._on_submission_view_requested(
                parent=widget,
                student_id=student_id,
            )
        )
        widget.exclusion_requested.connect(
            lambda: self._on_exclusion_requested(
                parent=widget,
                widget=widget,
                student_id=student_id,
                dialog_title="提出ファイルエラーへの処置",
            )
        )
        return widget

    def _on_submission_view_requested(
            self,
            *,
            parent: QWidget,
            student_id: StudentID,
    ) -> None:
        """既存の提出フォルダ表示経路を呼び、失敗時は利用者へ通知する。"""
        if not self._task_manager.is_empty():
            return
        try:
            self._main_window_facade.open_student_submission_folder(student_id)
        except Exception as error:
            self._logger.exception("提出フォルダを開けませんでした")
            QMessageBox.critical(
                parent,
                "提出フォルダを開く",
                f"提出フォルダを開けませんでした。\n{error}",
            )

    def _on_approval_requested(
            self,
            *,
            parent: QWidget,
            widget: SourceSafetyErrorWidget,
            student_id: StudentID,
            expected_sha256: str | None,
    ) -> None:
        """許可確認後にUseCaseを実行し、その結果をWidgetへ反映する。"""
        if expected_sha256 is None:
            return
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
        try:
            self._source_code_check_skip_approve_usecase.execute(
                student_id=student_id,
                expected_sha256=expected_sha256,
            )
        except SourceCodeCheckSkipApproveUseCaseError as error:
            widget.set_approval_state(str(error), enabled=False)
            return
        except Exception as error:
            self._logger.exception("ソースコードの許可を保存できませんでした")
            QMessageBox.critical(
                parent,
                "安全性チェックの許可",
                f"設定を保存できませんでした。\n{error}",
            )
            return
        widget.set_approval_state(
            "許可を保存しました。次に「実行」を押すとコンパイルを再試行します。",
            enabled=False,
        )

    def _on_exclusion_requested(
            self,
            *,
            parent: QWidget,
            widget: NotSubmittedErrorWidget | SubmissionFileRecoveryWidget,
            student_id: StudentID,
            dialog_title: str = "未提出学生への処置",
    ) -> None:
        """提出エラーの処置を確認し、UseCaseの結果をWidgetへ反映する。"""
        if not self._task_manager.is_empty():
            widget.set_exclusion_state(
                "実行中は処置できません。実行完了後に開き直してください。",
                enabled=False,
            )
            return

        current_mark = self._student_mark_get_usecase.execute(student_id)
        if current_mark.score is None:
            score_message = "未採点の状態から0点として保存します。"
        elif current_mark.score == 0:
            score_message = "現在の0点を維持します。"
        else:
            score_message = f"現在の{current_mark.score}点を0点で上書きします。"
        decision = QMessageBox.question(
            parent,
            dialog_title,
            f"{score_message}\n"
            "そのうえで、この学生を一括採点から除外します。\n"
            "この処置を実行しますか？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if decision != QMessageBox.Yes:
            return
        try:
            self._build_error_student_exclude_usecase.execute(student_id)
        except BuildErrorStudentExcludeUseCaseError as error:
            self._logger.exception("提出エラーへの処置を完了できませんでした")
            QMessageBox.critical(parent, dialog_title, str(error))
            widget.set_exclusion_state(
                str(error),
                enabled=self._task_manager.is_empty(),
            )
            return
        except Exception as error:
            self._logger.exception("提出エラーへの処置で予期しないエラーが発生しました")
            QMessageBox.critical(
                parent,
                dialog_title,
                f"処置を完了できませんでした。\n{error}",
            )
            return
        widget.set_exclusion_state(
            "0点と一括採点の除外設定を保存しました。",
            enabled=False,
        )
