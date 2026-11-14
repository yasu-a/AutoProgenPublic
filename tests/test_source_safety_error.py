"""安全性チェックのエラー詳細表示とソース単位の許可を検証する。"""

import hashlib
from unittest.mock import Mock

import pytest

from autoprogen.domain.error.stage.compile import (
    CompilerNotConfiguredError,
    SourceSafetyViolationError,
)
from autoprogen.domain.model.project_settings import ProjectSettings, SourceCodeCheckSkip
from autoprogen.domain.model.source_code import SourceCode
from autoprogen.domain.model.source_code_check import SourceCodeCheckFinding
from autoprogen.domain.model.value import StudentID
from autoprogen.usecase.dto.student_table_cell_data import StudentErrorCellDataTextEntry


STUDENT = StudentID("21D5109047B")
SOURCE = 'int main(void) {\n    system("echo hello");\n    return 0;\n}\n'
SOURCE_SHA = hashlib.sha256(SOURCE.encode("utf-8")).hexdigest()


def _source_code(source: str | None = SOURCE) -> SourceCode | None:
    """画面テスト用のソースコードモデルを作る。"""
    return SourceCode(text=source) if source is not None else None


def _safety_error(
        sha: str = SOURCE_SHA,
        line_numbers: tuple[int, ...] = (2, 4),
) -> SourceSafetyViolationError:
    """画面テスト用の構造化された安全性チェックエラーを作る。"""
    return SourceSafetyViolationError(
        source_sha256=sha,
        findings=tuple(
            SourceCodeCheckFinding(
                line_number=line_number,
                group_id="process",
                check_id="system",
            )
            for line_number in line_numbers
        ),
    )


@pytest.fixture
def qt_app(monkeypatch: pytest.MonkeyPatch):
    """画面を開かずにPyQtの表示を検証する。"""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PyQt5.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _make_widget(*, source: str | None = SOURCE, sha: str = SOURCE_SHA,
                 allowed: bool = True, already_approved: bool = False):
    """表示状態を指定した安全性チェック専用ウィジェットを作る。"""
    from autoprogen.control.widget_source_safety_error import SourceSafetyErrorWidget

    widget = SourceSafetyErrorWidget(
        source_code=_source_code(source),
        safety_errors=(_safety_error(sha),),
        show_editing_symbols=False,
        enable_line_wrap=False,
        can_approve=allowed,
        already_approved=already_approved,
    )
    return widget


def test_dialog_keeps_common_message_and_close_button(qt_app) -> None:
    """通常エラーは従来どおり、専用領域を表示しない。"""
    from autoprogen.control.dialog_student_error_detail import StudentErrorDetailDialog
    from PyQt5.QtWidgets import QDialogButtonBox, QWidget

    dialog = StudentErrorDetailDialog(
        student_id=STUDENT,
        error_entries=[StudentErrorCellDataTextEntry(
            summary_text="コンパイルに失敗しました。",
            detailed_text="コンパイルに失敗しました。",
        )],
    )
    assert "コンパイルに失敗しました。" in dialog._message_edit.toPlainText()
    assert dialog._extension_container.isHidden()
    assert dialog.findChild(QDialogButtonBox).button(QDialogButtonBox.Close)
    extension = QWidget()
    dialog.set_extension_widget(extension)
    assert extension.parent() is dialog._extension_container
    assert not dialog._extension_container.isHidden()
    dialog.set_extension_widget(None)
    assert dialog._extension_container.isHidden()
    dialog.close()


def _make_navigator_for_detail(error):
    """構造化エラーを一件返すNavigatorとProjectContainerを作る。"""
    from autoprogen.control.navigator import Navigator

    entry = StudentErrorCellDataTextEntry(
        summary_text="表示用の要約",
        detailed_text="表示用の詳細",
        error=error,
    )
    row = Mock()
    row.error_cell.text_entries = [entry]

    app_container = Mock()
    global_settings = Mock()
    global_settings.show_editing_symbols_in_source_code = False
    global_settings.enable_line_wrap_in_source_code = False
    app_container.global_settings_get_usecase.execute.return_value = global_settings

    project_container = Mock()
    project_container.student_table_load_usecase.execute_row.return_value = row
    project_container.student_source_code_get_usecase.execute.return_value = _source_code()
    project_container.project_settings_get_usecase.execute.return_value = (
        ProjectSettings.create_default()
    )
    project_container.task_manager.is_empty.return_value = True

    navigator = Navigator(app_container=app_container)
    navigator._current_project_container = project_container
    return navigator, project_container


def test_navigator_does_not_show_approval_for_regular_error(qt_app, monkeypatch) -> None:
    """通常の構造化エラーでは安全性チェックの許可UIを追加しない。"""
    from autoprogen.control.dialog_student_error_detail import StudentErrorDetailDialog

    navigator, container = _make_navigator_for_detail(CompilerNotConfiguredError())
    extension_widgets = []
    monkeypatch.setattr(StudentErrorDetailDialog, "exec_", lambda self: 0)
    monkeypatch.setattr(
        StudentErrorDetailDialog,
        "set_extension_widget",
        lambda self, widget: extension_widgets.append(widget),
    )

    navigator.open_student_error_detail_dialog(None, STUDENT)

    assert extension_widgets == []
    container.student_source_code_get_usecase.execute.assert_not_called()


def test_navigator_uses_structured_safety_error_for_approval_ui(
        qt_app,
        monkeypatch,
) -> None:
    """安全性チェック停止では構造化エラーを専用UIへ直接渡す。"""
    from autoprogen.control.dialog_student_error_detail import StudentErrorDetailDialog

    error = _safety_error()
    navigator, _ = _make_navigator_for_detail(error)
    extension_widgets = []
    monkeypatch.setattr(StudentErrorDetailDialog, "exec_", lambda self: 0)
    monkeypatch.setattr(
        StudentErrorDetailDialog,
        "set_extension_widget",
        lambda self, widget: extension_widgets.append((self, widget)),
    )

    navigator.open_student_error_detail_dialog(None, STUDENT)

    assert len(extension_widgets) == 1
    _, widget = extension_widgets[0]
    assert widget._source_view.toPlainText() == SOURCE
    assert [
        selection.cursor.blockNumber() + 1
        for selection in widget._source_view.extraSelections()
    ] == [2, 4]


def test_widget_highlights_detected_lines(qt_app) -> None:
    """黄色のハイライトが検出された行に設定される。"""
    widget = _make_widget()
    selections = widget._source_view.extraSelections()
    assert [selection.cursor.blockNumber() + 1 for selection in selections] == [2, 4]
    assert all(selection.format.background().color().name() == "#fff0a6" for selection in selections)
    assert widget._source_view.isReadOnly()
    assert widget._approve_button.isEnabled()
    widget.close()


@pytest.mark.parametrize("source,sha,allowed", [
    (SOURCE + "\n", SOURCE_SHA, True),
    (None, SOURCE_SHA, True),
    (SOURCE, SOURCE_SHA, False),
])
def test_widget_disables_unsafe_approval(qt_app, source, sha, allowed) -> None:
    """検査時の一致を証明できない場合や処理中には許可できない。"""
    widget = _make_widget(source=source, sha=sha, allowed=allowed)
    assert not widget._approve_button.isEnabled()
    widget.close()


def test_widget_disables_approval_for_conflicting_hashes(qt_app) -> None:
    """異なる検査対象のエラーが混在する場合は許可操作を無効にする。"""
    from autoprogen.control.widget_source_safety_error import SourceSafetyErrorWidget

    widget = SourceSafetyErrorWidget(
        source_code=_source_code(),
        safety_errors=(_safety_error(), _safety_error("a" * 64)),
        show_editing_symbols=False,
        enable_line_wrap=False,
    )
    try:
        assert not widget._approve_button.isEnabled()
    finally:
        widget.close()


def test_widget_emits_approval_request(qt_app) -> None:
    """許可ボタンを押すと保存処理を持たずに操作要求だけを通知する。"""
    widget = _make_widget()
    emitted = []
    widget.approval_requested.connect(lambda: emitted.append(True))
    widget._approve_button.click()
    assert emitted == [True]
    widget.close()


def _make_navigator_for_approval(source: str = SOURCE):
    """許可処理用UseCaseをMock化したNavigatorとProjectContainerを作る。"""
    from autoprogen.control.navigator import Navigator

    container = Mock()
    container.student_source_code_get_usecase.execute.return_value = SourceCode(text=source)
    container.project_settings_get_usecase.execute.return_value = ProjectSettings.create_default()
    navigator = Navigator(app_container=Mock())
    navigator._current_project_container = container
    return navigator, container


def test_approval_records_only_student_and_hash(qt_app, monkeypatch) -> None:
    """Navigatorは現在の設定を保持して許可した学生とハッシュだけを追加する。"""
    from PyQt5.QtWidgets import QMessageBox

    widget = _make_widget()
    navigator, container = _make_navigator_for_approval()
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Yes)
    navigator._approve_source_code_check_skip(
        parent=widget,
        widget=widget,
        student_id=STUDENT,
        displayed_source_code=SourceCode(text=SOURCE),
        expected_sha256=SOURCE_SHA,
    )
    updated = container.project_settings_put_usecase.execute.call_args.args[0]
    assert SourceCodeCheckSkip(student_id=STUDENT, source_sha256=SOURCE_SHA) in updated.source_code_check_skips
    assert (
        updated.suppressed_source_code_checks
        == container.project_settings_get_usecase.execute.return_value.suppressed_source_code_checks
    )
    assert not widget._approve_button.isEnabled()
    widget.close()


def test_approval_rechecks_source_before_saving(qt_app) -> None:
    """ダイアログを開いた後にソースが変わったら設定を書き込まない。"""
    widget = _make_widget()
    navigator, container = _make_navigator_for_approval(SOURCE + "changed")
    navigator._approve_source_code_check_skip(
        parent=widget,
        widget=widget,
        student_id=STUDENT,
        displayed_source_code=SourceCode(text=SOURCE),
        expected_sha256=SOURCE_SHA,
    )
    container.project_settings_put_usecase.execute.assert_not_called()
    assert not widget._approve_button.isEnabled()
    widget.close()
