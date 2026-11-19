import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QCheckBox, QDialog, QPushButton

from autoprogen.control.dialog_usage_notice import UsageNoticeDialog
from autoprogen.control.widget_usage_notice import USAGE_NOTICE_ITEMS


@pytest.fixture
def qt_app(monkeypatch: pytest.MonkeyPatch) -> QApplication:
    """画面を表示せずに利用できるQApplicationを返す。"""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_usage_notice_dialog_accepts_after_all_items_are_confirmed(
        qt_app: QApplication,
) -> None:
    """全項目を確認するまでプロジェクトを開く操作を許可しない。"""
    dialog = UsageNoticeDialog(app_version_text="1.2-beta.1")
    checkboxes = dialog.notice_widget.findChildren(QCheckBox)
    accept_button = dialog.findChild(QPushButton, "acceptUsageNotice")

    assert len(checkboxes) == len(USAGE_NOTICE_ITEMS)
    assert accept_button is not None
    assert not accept_button.isEnabled()

    for checkbox in checkboxes:
        checkbox.setChecked(True)

    assert accept_button.isEnabled()

    accept_button.click()

    assert dialog.result() == QDialog.Accepted


def test_usage_notice_dialog_can_be_rejected_without_confirmation(
        qt_app: QApplication,
) -> None:
    """項目を確認していなくてもプロジェクトを開かず戻れる。"""
    dialog = UsageNoticeDialog(app_version_text="1.2-beta.1")
    reject_button = dialog.findChild(QPushButton, "rejectUsageNotice")

    assert reject_button is not None
    reject_button.click()

    assert dialog.result() == QDialog.Rejected


def test_usage_notice_widget_emits_current_confirmation_state(
        qt_app: QApplication,
) -> None:
    """確認を外した場合も全項目の確認状態をダイアログへ反映する。"""
    dialog = UsageNoticeDialog(app_version_text="1.2-beta.1")
    checkboxes = dialog.notice_widget.findChildren(QCheckBox)
    accept_button = dialog.findChild(QPushButton, "acceptUsageNotice")

    for checkbox in checkboxes:
        checkbox.setCheckState(Qt.Checked)
    checkboxes[-1].setCheckState(Qt.Unchecked)

    assert accept_button is not None
    assert not accept_button.isEnabled()
