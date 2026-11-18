"""学生エラー詳細CoordinatorのWidget構成と操作接続を検証する。"""

import hashlib
from unittest.mock import Mock

import pytest
from PyQt5.QtWidgets import QApplication, QMessageBox, QPushButton

from autoprogen.control.coordinator_student_error_detail import (
    StudentErrorDetailCoordinator,
)
from autoprogen.domain.error.stage.build import SubmissionNotFoundError
from autoprogen.domain.error.stage.compile import (
    CompilerNotConfiguredError,
    SourceSafetyViolationError,
)
from autoprogen.domain.model.project_settings import ProjectSettings
from autoprogen.domain.model.source_code import SourceCode
from autoprogen.domain.model.source_code_check import SourceCodeCheckFinding
from autoprogen.domain.model.student_mark import StudentMark
from autoprogen.domain.model.value import StudentID
from autoprogen.usecase.dto.student_table_cell_data import (
    StudentErrorCellData,
    StudentErrorCellDataTextEntry,
)
from autoprogen.usecase.source_code_check_skip import (
    SourceCodeCheckSkipApproveUseCaseError,
)


STUDENT = StudentID("21D5109047B")
OTHER_STUDENT = StudentID("21D5109048C")
SOURCE_TEXT = 'int main(void) {\n    system("echo hello");\n    return 0;\n}\n'
SOURCE_SHA = hashlib.sha256(SOURCE_TEXT.encode("utf-8")).hexdigest()


@pytest.fixture
def qt_app(monkeypatch: pytest.MonkeyPatch) -> QApplication:
    """画面を表示せずに利用できるQApplicationを返す。"""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _safety_error() -> SourceSafetyViolationError:
    """表示確認用の安全性チェックエラーを返す。"""
    return SourceSafetyViolationError(
        source_sha256=SOURCE_SHA,
        findings=(SourceCodeCheckFinding(
            line_number=2,
            group_id="process",
            check_id="system",
        ),),
    )


def _row(student_id: StudentID, errors: list[Exception]) -> Mock:
    """指定した構造化エラーを持つ学生行を返す。"""
    row = Mock()
    row.error_cell = StudentErrorCellData(
        student_id=student_id,
        text_entries=[
            StudentErrorCellDataTextEntry(
                summary_text=f"{type(error).__name__}の要約",
                detailed_text=f"{type(error).__name__}の詳細",
                error=error,
            )
            for error in errors
        ],
    )
    return row


def _make_coordinator(
        *errors: Exception,
        student_id: StudentID = STUDENT,
) -> tuple[StudentErrorDetailCoordinator, dict[str, Mock]]:
    """指定エラーを表示するCoordinatorと依存Mockを返す。"""
    dependencies = {
        "facade": Mock(),
        "source_get": Mock(),
        "global_settings_get": Mock(),
        "project_settings_get": Mock(),
        "approve": Mock(),
        "exclude": Mock(),
        "mark_get": Mock(),
        "task_manager": Mock(),
    }
    dependencies["facade"].load_student_table_row.return_value = _row(
        student_id,
        list(errors),
    )
    dependencies["source_get"].execute.return_value = SourceCode(text=SOURCE_TEXT)
    global_settings = Mock(
        show_editing_symbols_in_source_code=False,
        enable_line_wrap_in_source_code=False,
    )
    dependencies["global_settings_get"].execute.return_value = global_settings
    dependencies["project_settings_get"].execute.return_value = (
        ProjectSettings.create_default()
    )
    dependencies["mark_get"].execute.return_value = StudentMark(student_id, None)
    dependencies["task_manager"].is_empty.return_value = True
    coordinator = StudentErrorDetailCoordinator(
        main_window_facade=dependencies["facade"],
        student_source_code_get_usecase=dependencies["source_get"],
        global_settings_get_usecase=dependencies["global_settings_get"],
        project_settings_get_usecase=dependencies["project_settings_get"],
        source_code_check_skip_approve_usecase=dependencies["approve"],
        not_submitted_student_exclude_usecase=dependencies["exclude"],
        student_mark_get_usecase=dependencies["mark_get"],
        task_manager=dependencies["task_manager"],
    )
    return coordinator, dependencies


def test_regular_error_uses_only_common_detail_widget(qt_app: QApplication) -> None:
    """通常エラーには専用の操作Widgetを追加しない。"""
    coordinator, dependencies = _make_coordinator(CompilerNotConfiguredError())

    detail = coordinator.create_widget(None, STUDENT)

    assert detail is not None
    assert detail._extension_container.isHidden()
    dependencies["source_get"].execute.assert_not_called()
    detail.close()


def test_safety_error_builds_source_widget_and_delegates_approval(
        qt_app: QApplication,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """安全性チェック停止はソースを表示し、許可要求を専用UseCaseへ渡す。"""
    coordinator, dependencies = _make_coordinator(_safety_error())
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.Yes,
    )

    detail = coordinator.create_widget(None, STUDENT)
    widget = detail._extension_widget
    widget._approve_button.click()

    assert widget._source_view.toPlainText() == SOURCE_TEXT
    assert [
        selection.cursor.blockNumber() + 1
        for selection in widget._source_view.extraSelections()
    ] == [2]
    dependencies["approve"].execute.assert_called_once_with(
        student_id=STUDENT,
        expected_sha256=SOURCE_SHA,
    )
    assert not widget._approve_button.isEnabled()
    detail.close()


def test_approval_cancel_and_rejection_keep_ui_consistent(
        qt_app: QApplication,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """キャンセルでは保存せず、UseCaseの拒否理由はWidgetへ表示する。"""
    coordinator, dependencies = _make_coordinator(_safety_error())
    detail = coordinator.create_widget(None, STUDENT)
    widget = detail._extension_widget
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.No,
    )
    widget._approve_button.click()
    dependencies["approve"].execute.assert_not_called()
    assert widget._approve_button.isEnabled()

    dependencies["approve"].execute.side_effect = (
        SourceCodeCheckSkipApproveUseCaseError("ソースコードが更新されました。")
    )
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.Yes,
    )
    widget._approve_button.click()
    assert "更新されました" in widget._status_label.text()
    assert not widget._approve_button.isEnabled()
    detail.close()


def test_approval_save_failure_is_shown_in_dialog(
        qt_app: QApplication,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """許可設定の保存失敗は成功表示にせずダイアログで通知する。"""
    coordinator, dependencies = _make_coordinator(_safety_error())
    dependencies["approve"].execute.side_effect = OSError("write failed")
    critical = Mock()
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.Yes,
    )
    monkeypatch.setattr(QMessageBox, "critical", critical)

    detail = coordinator.create_widget(None, STUDENT)
    widget = detail._extension_widget
    widget._approve_button.click()

    assert "write failed" in critical.call_args.args[2]
    assert "許可を保存しました" not in widget._status_label.text()
    detail.close()


def test_not_submitted_action_confirms_overwrite_and_delegates_exclusion(
        qt_app: QApplication,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """未提出学生の既存点数を明示し、確認後に除外UseCaseへ渡す。"""
    coordinator, dependencies = _make_coordinator(SubmissionNotFoundError())
    dependencies["mark_get"].execute.return_value = StudentMark(STUDENT, 70)
    question = Mock(return_value=QMessageBox.Yes)
    monkeypatch.setattr(QMessageBox, "question", question)

    detail = coordinator.create_widget(None, STUDENT)
    widget = detail._extension_widget
    widget._exclude_button.click()

    assert "現在の70点を0点で上書きします" in question.call_args.args[2]
    dependencies["exclude"].execute.assert_called_once_with(STUDENT)
    assert not widget._exclude_button.isEnabled()
    detail.close()


def test_not_submitted_action_cancel_does_not_call_usecase(
        qt_app: QApplication,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """未提出学生への処置をキャンセルした場合は保存を開始しない。"""
    coordinator, dependencies = _make_coordinator(SubmissionNotFoundError())
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.No,
    )

    detail = coordinator.create_widget(None, STUDENT)
    detail._extension_widget._exclude_button.click()

    dependencies["exclude"].execute.assert_not_called()
    assert detail._extension_widget._exclude_button.isEnabled()
    detail.close()


def test_not_submitted_action_is_disabled_while_running(
        qt_app: QApplication,
) -> None:
    """実行中は未提出学生への処置を開始できない。"""
    coordinator, dependencies = _make_coordinator(SubmissionNotFoundError())
    dependencies["task_manager"].is_empty.return_value = False

    detail = coordinator.create_widget(None, STUDENT)

    assert not detail._extension_widget._exclude_button.isEnabled()
    detail.close()


def test_safety_and_not_submitted_widgets_can_coexist(
        qt_app: QApplication,
) -> None:
    """異なる専用処置が必要な場合も両方のWidgetを保持する。"""
    coordinator, _ = _make_coordinator(
        _safety_error(),
        SubmissionNotFoundError(),
    )

    detail = coordinator.create_widget(None, STUDENT)

    assert detail.findChild(QPushButton, "approveSourceSafetySkip") is not None
    assert detail.findChild(QPushButton, "excludeNotSubmittedStudent") is not None
    detail.close()


def test_signal_connections_keep_each_student_id(
        qt_app: QApplication,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """複数学生のWidgetを生成しても許可対象の学生を取り違えない。"""
    coordinator, dependencies = _make_coordinator(_safety_error())
    dependencies["facade"].load_student_table_row.side_effect = (
        _row(STUDENT, [_safety_error()]),
        _row(OTHER_STUDENT, [_safety_error()]),
    )
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.Yes,
    )

    first = coordinator.create_widget(None, STUDENT)
    second = coordinator.create_widget(None, OTHER_STUDENT)
    first._extension_widget._approve_button.click()
    second._extension_widget._approve_button.click()

    assert dependencies["approve"].execute.call_args_list[0].kwargs["student_id"] == STUDENT
    assert (
        dependencies["approve"].execute.call_args_list[1].kwargs["student_id"]
        == OTHER_STUDENT
    )
    first.close()
    second.close()
