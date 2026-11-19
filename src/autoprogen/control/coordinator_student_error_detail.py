"""学生エラー詳細Widgetの構成と、UI上の処置確認を担当する。"""

from collections.abc import Callable

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QVBoxLayout, QWidget

from autoprogen.control.widget_error_extension import ErrorExtensionWidget
from autoprogen.control.widget_error_navigation import ErrorNavigationWidget
from autoprogen.control.widget_not_submitted_error import NotSubmittedErrorWidget
from autoprogen.control.widget_source_safety_error import SourceSafetyErrorWidget
from autoprogen.control.widget_student_error_detail import StudentErrorDetailWidget
from autoprogen.control.widget_submission_file_recovery import SubmissionFileRecoveryWidget
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
from autoprogen.domain.model.value import StudentID
from autoprogen.usecase.main_window import MainWindowFacade, StudentErrorActionRefused
from autoprogen.util.app_logging import create_logger


class StudentErrorDetailCoordinator(QObject):
    """エラーに応じたWidgetを組み立て、GUI操作と画面遷移要求を通知する。"""

    _logger = create_logger()

    # 実際の画面遷移はNavigatorを持つMainWindowに委ねる。
    global_settings_requested = pyqtSignal(name="global_settings_requested")
    testcase_list_requested = pyqtSignal(name="testcase_list_requested")
    submission_folder_requested = pyqtSignal(StudentID, name="submission_folder_requested")

    _SUBMISSION_FILE_ERRORS = (
        SourceFilenameMultipleNumbersError,
        SourceFilenameNoNumberError,
        MultipleSourceFilesError,
        SubmissionSourceNotFoundError,
        SourceEncodingUnknownError,
    )
    _GLOBAL_SETTING_ERRORS = (
        CompilerNotConfiguredError,
        VsDevToolNotFoundError,
        CompilerTimeoutError,
    )
    _TESTCASE_SETTING_ERRORS = (ExecutionTimeoutError, OutputMatchingError)

    def __init__(self, *, main_window_facade: MainWindowFacade) -> None:
        """Widget表示と業務操作の窓口となるFacadeだけを受け取る。"""
        super().__init__()
        self._facade = main_window_facade

    def create_widget(self, parent: QWidget, student_id: StudentID) -> QWidget | None:
        """対象学生のエラーを一度取得し、必要な補助Widgetだけを付加する。"""
        row = self._facade.load_student_table_row(student_id)
        if not row.error_cell.text_entries:
            return None
        entries = row.error_cell.distinct_text_entries()
        detail = StudentErrorDetailWidget(parent, error_entries=entries)
        extensions: list[ErrorExtensionWidget] = []

        safety_errors = tuple(
            entry.error for entry in entries
            if isinstance(entry.error, SourceSafetyViolationError)
        )
        if safety_errors:
            extensions.append(self._create_source_safety_widget(
                detail, student_id, safety_errors,
            ))

        if any(isinstance(entry.error, SubmissionNotFoundError) for entry in entries):
            extensions.append(self._create_not_submitted_widget(
                detail, student_id, row.bulk_grading_skipped,
            ))

        if any(isinstance(entry.error, self._SUBMISSION_FILE_ERRORS) for entry in entries):
            extensions.append(self._create_submission_recovery_widget(
                detail, student_id, row.bulk_grading_skipped,
            ))

        if any(isinstance(entry.error, self._GLOBAL_SETTING_ERRORS) for entry in entries):
            extensions.append(self._create_navigation_widget(
                detail,
                message=(
                    "グローバル設定の確認が必要です。\n"
                    "コンパイラのパスやコンパイル時間制限を確認してください。"
                ),
                button_text="グローバル設定を開く",
                on_request=self.global_settings_requested.emit,
            ))

        if any(isinstance(entry.error, self._TESTCASE_SETTING_ERRORS) for entry in entries):
            extensions.append(self._create_navigation_widget(
                detail,
                message=(
                    "テストケースの確認が必要です。\n"
                    "入力内容、実行時間制限、期待する出力を確認してください。"
                ),
                button_text="テストケース一覧を開く",
                on_request=self.testcase_list_requested.emit,
            ))

        if len(extensions) == 1:
            detail.set_extension_widget(extensions[0])
        elif extensions:
            container = QWidget(detail)
            layout = QVBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(8)
            for widget in extensions:
                layout.addWidget(widget)
            detail.set_extension_widget(container)
        return detail

    @staticmethod
    def _create_navigation_widget(
            parent: QWidget,
            *,
            message: str,
            button_text: str,
            on_request: Callable[[], None],
    ) -> ErrorNavigationWidget:
        """遷移先の種類をWidget継承ではなくSignal接続で表現する。"""
        widget = ErrorNavigationWidget(parent, message=message, button_text=button_text)
        widget.navigation_requested.connect(on_request)
        return widget

    def _create_source_safety_widget(
            self,
            parent: QWidget,
            student_id: StudentID,
            safety_errors: tuple[SourceSafetyViolationError, ...],
    ) -> SourceSafetyErrorWidget:
        """Facadeから取得した表示情報で安全性チェックWidgetを組み立てる。"""
        data = self._facade.get_source_safety_display_data(student_id, safety_errors)
        widget = SourceSafetyErrorWidget(
            parent,
            source_code=data.source_code,
            safety_errors=safety_errors,
            show_editing_symbols=data.show_editing_symbols,
            enable_line_wrap=data.enable_line_wrap,
            can_approve=data.can_approve,
            already_approved=data.already_approved,
        )
        widget.approval_requested.connect(
            lambda: self._on_approval_requested(
                widget=widget,
                student_id=student_id,
                expected_sha256=data.source_sha256,
            )
        )
        return widget

    def _create_not_submitted_widget(
            self,
            parent: QWidget,
            student_id: StudentID,
            already_excluded: bool,
    ) -> NotSubmittedErrorWidget:
        """未提出時の既存Widgetを維持し、共通の除外処置につなぐ。"""
        widget = NotSubmittedErrorWidget(
            parent,
            can_exclude=self._facade.can_perform_student_error_action(),
            already_excluded=already_excluded,
        )
        widget.exclusion_requested.connect(
            lambda: self._on_exclusion_requested(
                widget=widget,
                student_id=student_id,
                dialog_title="未提出学生への処置",
            )
        )
        return widget

    def _create_submission_recovery_widget(
            self,
            parent: QWidget,
            student_id: StudentID,
            already_excluded: bool,
    ) -> SubmissionFileRecoveryWidget:
        """提出ファイルの確認と0点除外を共通Widgetに接続する。"""
        widget = SubmissionFileRecoveryWidget(
            parent,
            can_exclude=self._facade.can_perform_student_error_action(),
            already_excluded=already_excluded,
        )
        widget.submission_view_requested.connect(
            lambda: self.submission_folder_requested.emit(student_id)
        )
        widget.exclusion_requested.connect(
            lambda: self._on_exclusion_requested(
                widget=widget,
                student_id=student_id,
                dialog_title="提出ファイルエラーへの処置",
            )
        )
        return widget

    def _on_approval_requested(
            self,
            *,
            widget: SourceSafetyErrorWidget,
            student_id: StudentID,
            expected_sha256: str | None,
    ) -> None:
        """利用者の確認を受け、Facadeに安全性チェック許可を依頼する。"""
        if expected_sha256 is None:
            return
        if not self._facade.can_perform_student_error_action():
            widget.set_approval_state("実行中は処置できません。", enabled=False)
            return
        choice = QMessageBox.question(
            widget,
            "安全性チェックの許可",
            "この学生の現在のソースコードだけを許可しますか？\n"
            "次回実行時に安全性チェックを省略します。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if choice != QMessageBox.Yes:
            return
        try:
            self._facade.approve_source_code_check(student_id, expected_sha256)
        except StudentErrorActionRefused as error:
            widget.set_approval_state(str(error), enabled=False)
            return
        except Exception as error:
            self._logger.exception("ソースコードの許可を保存できませんでした")
            QMessageBox.critical(
                widget, "安全性チェックの許可", f"設定を保存できませんでした。\n{error}"
            )
            return
        widget.set_approval_state(
            "許可を保存しました。次に「実行」を押すとコンパイルを再試行します。",
            enabled=False,
        )

    def _on_exclusion_requested(
            self,
            *,
            widget: NotSubmittedErrorWidget | SubmissionFileRecoveryWidget,
            student_id: StudentID,
            dialog_title: str,
    ) -> None:
        """点数の上書きを確認し、Facadeに0点保存・採点除外を依頼する。"""
        if not self._facade.can_perform_student_error_action():
            widget.set_exclusion_state(
                "実行中は処置できません。実行完了後に開き直してください。",
                enabled=False,
            )
            return
        try:
            score = self._facade.get_student_mark_score(student_id)
        except Exception as error:
            self._logger.exception("現在の点数を取得できませんでした")
            QMessageBox.critical(widget, dialog_title, str(error))
            return
        if score is None:
            score_message = "未採点の状態から0点として保存します。"
        elif score == 0:
            score_message = "現在の0点を維持します。"
        else:
            score_message = f"現在の{score}点を0点で上書きします。"
        choice = QMessageBox.question(
            widget,
            dialog_title,
            f"{score_message}\n"
            "そのうえで、この学生を一括採点から除外します。\n"
            "この処置を実行しますか？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if choice != QMessageBox.Yes:
            return
        try:
            self._facade.exclude_build_error_student(student_id)
        except StudentErrorActionRefused as error:
            self._logger.warning("提出エラーへの処置を完了できませんでした: %s", error)
            QMessageBox.critical(widget, dialog_title, str(error))
            widget.set_exclusion_state(
                str(error),
                enabled=self._facade.can_perform_student_error_action(),
            )
            return
        except Exception as error:
            self._logger.exception("提出エラーへの処置で予期しないエラーが発生しました")
            QMessageBox.critical(widget, dialog_title, f"処置を完了できませんでした。\n{error}")
            return
        widget.set_exclusion_state(
            "0点と一括採点の除外設定を保存しました。",
            enabled=False,
        )
