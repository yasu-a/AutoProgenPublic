import pytest

from autoprogen.usecase.dto.student_table_cell_data import StudentErrorCellDataTextEntry


@pytest.fixture
def qt_app(monkeypatch: pytest.MonkeyPatch):
    """ディスプレイを使わずQtウィジェットを検証する。"""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PyQt5.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_detail_widget_displays_all_messages_read_only(qt_app) -> None:
    """詳細Widgetは複数エラーを編集不可のテキストで表示する。"""
    from autoprogen.control.widget_student_error_detail import StudentErrorDetailWidget

    widget = StudentErrorDetailWidget(
        error_entries=[
            StudentErrorCellDataTextEntry("最初のエラー", "最初のエラー\n詳細A"),
            StudentErrorCellDataTextEntry("次のエラー", "詳細B"),
        ],
    )
    displayed = widget._message_edit.toPlainText()
    assert "最初のエラー\n詳細A" in displayed
    assert "次のエラー\n詳細B" in displayed
    assert widget._message_edit.isReadOnly()
    widget.close()
