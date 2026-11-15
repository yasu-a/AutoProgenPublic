from unittest.mock import Mock

import pytest
from PyQt5.QtWidgets import QApplication, QDialog

from autoprogen.control.dialog_settings_edit import AbstractSettingsEditDialog


class _SettingsEditDialog(AbstractSettingsEditDialog[int]):
    """共通設定ダイアログの動作確認に使用する最小実装。"""

    def __init__(self) -> None:
        """現在値と保存先を初期化する。"""
        super().__init__()
        self.current_data = 0
        self.save_data_mock = Mock()
        self.add_standard_buttons()

    def _set_data(self, data: int) -> None:
        """テスト用の現在値を設定する。"""
        self.current_data = data

    def get_data(self) -> int:
        """テスト用の現在値を返す。"""
        return self.current_data

    def save_data(self, data: int) -> None:
        """保存された値をMockへ記録する。"""
        self.save_data_mock(data)


@pytest.fixture
def qt_app(monkeypatch: pytest.MonkeyPatch) -> QApplication:
    """画面を表示しないQtテスト用アプリを返す。"""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_settings_dialog_saves_changed_data(qt_app: QApplication) -> None:
    """保存操作で変更後の値だけを永続化してダイアログを閉じる。"""
    dialog = _SettingsEditDialog()
    dialog.set_data(1)
    dialog.current_data = 2

    dialog._save()

    dialog.save_data_mock.assert_called_once_with(2)
    assert dialog.has_changes is True
    assert dialog.result() == QDialog.Accepted


def test_settings_dialog_does_not_save_unchanged_data(qt_app: QApplication) -> None:
    """値が変わっていない場合は保存せずダイアログを閉じる。"""
    dialog = _SettingsEditDialog()
    dialog.set_data(1)

    dialog._save()

    dialog.save_data_mock.assert_not_called()
    assert dialog.has_changes is False
    assert dialog.result() == QDialog.Accepted


def test_settings_dialog_confirms_discard_before_rejecting(
        qt_app: QApplication,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """変更後のキャンセルでは、破棄が選択された場合だけ閉じる。"""
    dialog = _SettingsEditDialog()
    dialog.set_data(1)
    dialog.current_data = 2
    dialog.show()
    confirmation = Mock(return_value=False)
    monkeypatch.setattr(dialog, "_confirm_close_without_saving", confirmation)

    dialog.reject()

    assert dialog.isVisible()
    confirmation.return_value = True
    dialog.reject()
    assert not dialog.isVisible()
    dialog.save_data_mock.assert_not_called()


def test_settings_dialog_close_uses_discard_confirmation(
        qt_app: QApplication,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """×ボタン相当の終了操作でも未保存変更の破棄を確認する。"""
    dialog = _SettingsEditDialog()
    dialog.set_data(1)
    dialog.current_data = 2
    dialog.show()
    confirmation = Mock(return_value=False)
    monkeypatch.setattr(dialog, "_confirm_close_without_saving", confirmation)

    dialog.close()

    confirmation.assert_called_once()
    assert dialog.isVisible()
    confirmation.return_value = True
    dialog.reject()
