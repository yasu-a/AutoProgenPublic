"""安全性チェックのエラー詳細表示とソース単位の許可を検証する。"""

import hashlib

import pytest

from autoprogen.domain.error.stage.compile import SourceSafetyViolationError
from autoprogen.domain.model.source_code import SourceCode
from autoprogen.domain.model.source_code_check import SourceCodeCheckFinding
from autoprogen.domain.model.value import StudentID
from autoprogen.usecase.dto.student_table_cell_data import (
    StudentErrorCellDataTextEntry,
)


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


def test_detail_widget_keeps_common_message_and_optional_extension(qt_app) -> None:
    """通常エラーでは専用領域を隠し、必要な場合だけ追加Widgetを表示する。"""
    from PyQt5.QtWidgets import QWidget
    from autoprogen.control.widget_student_error_detail import StudentErrorDetailWidget

    detail_widget = StudentErrorDetailWidget(
        error_entries=[StudentErrorCellDataTextEntry(
            summary_text="コンパイルに失敗しました。",
            detailed_text="コンパイルに失敗しました。",
        )],
    )
    assert "コンパイルに失敗しました。" in detail_widget._message_edit.toPlainText()
    assert detail_widget._extension_container.isHidden()
    extension = QWidget()
    detail_widget.set_extension_widget(extension)
    assert extension.parent() is detail_widget._extension_container
    assert not detail_widget._extension_container.isHidden()
    detail_widget.set_extension_widget(None)
    assert detail_widget._extension_container.isHidden()
    detail_widget.close()


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


def test_widget_disables_approval_when_already_approved(qt_app) -> None:
    """同じ学生とソースが許可済みの場合は許可操作を無効にする。"""
    widget = _make_widget(already_approved=True)

    assert not widget._approve_button.isEnabled()
    assert "すでに許可されています" in widget._status_label.text()
    widget.close()
