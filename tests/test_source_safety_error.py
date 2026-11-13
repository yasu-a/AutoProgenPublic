"""安全性チェックのエラー詳細表示とソース単位の許可を検証する。"""

import hashlib
from unittest.mock import Mock

import pytest

from autoprogen.control.student_error_detail_parser import (
    SAFETY_ERROR_PREFIX,
    SourceSafetyErrorDetails,
    parse_safety_check_error,
)
from autoprogen.domain.model.project_settings import ProjectSettings, SourceCodeCheckSkip
from autoprogen.domain.model.source_code import SourceCode
from autoprogen.domain.model.value import StudentID
from autoprogen.usecase.dto.student_table_cell_data import StudentErrorCellDataTextEntry


STUDENT = StudentID("21D5109047B")
SOURCE = 'int main(void) {\n    system("echo hello");\n    return 0;\n}\n'
SOURCE_SHA = hashlib.sha256(SOURCE.encode("utf-8")).hexdigest()


def _source_code(source: str | None = SOURCE) -> SourceCode | None:
    """画面テスト用のソースコードモデルを作る。"""
    return SourceCode(text=source) if source is not None else None


def _entry(message: str) -> StudentErrorCellDataTextEntry:
    """COMPILE失敗結果相当のエラーを作る。"""
    return StudentErrorCellDataTextEntry(summary_text=message, detailed_text=message)


def _message(sha: str | None = SOURCE_SHA) -> str:
    """検出行が複数あるメッセージを作る。"""
    suffix = f"\n検査対象SHA-256: {sha}" if sha is not None else ""
    return SAFETY_ERROR_PREFIX + suffix + "\n2行目: [process.system] 外部コマンドの実行\n4行目: [x.y] 検出"


def test_parser_recognizes_only_safety_errors() -> None:
    """コンパイルエラーの文言が似ていても専用表示にしない。"""
    assert parse_safety_check_error([_entry("コンパイルに失敗しました。")]) is None
    assert parse_safety_check_error([_entry(_message())]) == SourceSafetyErrorDetails(
        source_sha256=SOURCE_SHA, line_numbers=(2, 4),
    )


def test_parser_handles_old_message_without_hash() -> None:
    """旧エラーの行番号を表示しつつ許可に必要なハッシュは欠落とする。"""
    assert parse_safety_check_error([_entry(_message(None))]) == SourceSafetyErrorDetails(
        source_sha256=None, line_numbers=(2, 4),
    )


def test_parser_rejects_ambiguous_hashes() -> None:
    """異なる検査結果が混在しても許可用ハッシュを決め打ちしない。"""
    other_sha = "a" * 64 if SOURCE_SHA != "a" * 64 else "b" * 64
    result = parse_safety_check_error([_entry(_message()), _entry(_message(other_sha))])
    assert result is not None
    assert result.source_sha256 is None


@pytest.fixture
def qt_app(monkeypatch: pytest.MonkeyPatch):
    """画面を開かずにPyQtの表示を検証する。"""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PyQt5.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _make_widget(*, source: str | None = SOURCE, sha: str | None = SOURCE_SHA,
                 allowed: bool = True, already_approved: bool = False):
    """表示状態を指定した安全性チェック専用ウィジェットを作る。"""
    from autoprogen.control.widget_source_safety_error import SourceSafetyErrorWidget

    widget = SourceSafetyErrorWidget(
        source_code=_source_code(source),
        safety_error=SourceSafetyErrorDetails(sha, (2, 4)),
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
        error_entries=[_entry("コンパイルに失敗しました。")],
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
    (SOURCE, None, True),
    (None, SOURCE_SHA, True),
    (SOURCE, SOURCE_SHA, False),
])
def test_widget_disables_unsafe_approval(qt_app, source, sha, allowed) -> None:
    """検査時の一致を証明できない場合や処理中には許可できない。"""
    widget = _make_widget(source=source, sha=sha, allowed=allowed)
    assert not widget._approve_button.isEnabled()
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
