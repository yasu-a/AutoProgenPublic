"""テスト結果の空ストリームに対する表示を検証する。"""

from unittest.mock import Mock

import pytest
from PyQt5.QtWidgets import QApplication

from autoprogen.control.widget_testcase_result_otuput_file_view import (
    TestCaseResultOutputFileViewWidget,
)
from autoprogen.domain.model.output_file import OutputFile
from autoprogen.domain.model.value import FileID

TestCaseResultOutputFileViewWidget.__test__ = False


@pytest.fixture
def qt_app(monkeypatch: pytest.MonkeyPatch) -> QApplication:
    """画面を表示せずに利用できるQApplicationを返す。"""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _create_widget() -> TestCaseResultOutputFileViewWidget:
    """表示設定を無効にしたテスト用Widgetを返す。"""
    settings = Mock(
        show_editing_symbols_in_stream_content=False,
        enable_line_wrap_in_stream_content=False,
    )
    global_settings_get_usecase = Mock()
    global_settings_get_usecase.execute.return_value = settings
    return TestCaseResultOutputFileViewWidget(
        global_settings_get_usecase=global_settings_get_usecase,
    )


def _empty_output_entry(file_id: FileID) -> Mock:
    """内容が空の実出力を持つテスト結果Entryを返す。"""
    entry = Mock()
    entry.file_id = file_id
    entry.has_actual = True
    entry.has_expected = True
    entry.actual = OutputFile(file_id=file_id, content=b"")
    entry.test_result.matched_tokens = []
    return entry


def test_empty_output_is_shown_as_red_warning(qt_app: QApplication) -> None:
    """空の標準出力は本文ではなく上部の警告欄へ表示する。"""
    widget = _create_widget()

    widget.set_data(_empty_output_entry(FileID.STDOUT))

    assert widget._l_messages.isVisibleTo(widget)
    assert "このストリームへの出力がありません" in widget._l_messages.text()
    assert "Visual Studio" in widget._l_messages.text()
    assert widget._te.toPlainText() == ""


def test_empty_stdin_is_shown_as_warning(qt_app: QApplication) -> None:
    """空の標準入力も本文へ説明を混ぜず警告欄へ表示する。"""
    widget = _create_widget()

    widget.set_data(_empty_output_entry(FileID.STDIN))

    assert widget._l_messages.isVisibleTo(widget)
    assert "標準入力は空です" in widget._l_messages.text()
    assert "Visual Studio" not in widget._l_messages.text()
    assert widget._te.toPlainText() == ""


def test_invalid_utf8_is_shown_with_visual_studio_guidance(
        qt_app: QApplication,
) -> None:
    """不正なUTF-8をエスケープ表示してVisual Studioでの確認を案内する。"""
    entry = _empty_output_entry(FileID.STDOUT)
    entry.actual = OutputFile(file_id=FileID.STDOUT, content=b"result: \x81\xff")
    widget = _create_widget()

    widget.set_data(entry)

    assert "このストリームの文字コードが不明です" in widget._l_messages.text()
    assert "Visual Studio" in widget._l_messages.text()
    assert widget._te.toPlainText() == r"result: \x81\xff"
