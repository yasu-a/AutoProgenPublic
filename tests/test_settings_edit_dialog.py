from unittest.mock import Mock

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox

from autoprogen.control.dialog_settings_edit import AbstractSettingsEditDialog
from autoprogen.domain.model.global_settings import GlobalSettings
from autoprogen.domain.model.project_settings import (
    ProjectSettings,
    SourceCodeCheckIdentifier,
)
from autoprogen.domain.model.testcase_config import TestCaseConfig as CaseConfig
from autoprogen.domain.model.value import TestCaseID as CaseID
from autoprogen.domain.service.source_code_check_factory import SourceCodeCheckCatalogFactory


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
    confirmation = Mock(return_value=QMessageBox.Cancel)
    monkeypatch.setattr(dialog, "_confirm_unsaved_changes", confirmation)

    dialog.reject()

    assert dialog.isVisible()
    confirmation.return_value = QMessageBox.Discard
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
    confirmation = Mock(return_value=QMessageBox.Cancel)
    monkeypatch.setattr(dialog, "_confirm_unsaved_changes", confirmation)

    dialog.close()

    confirmation.assert_called_once()
    assert dialog.isVisible()
    confirmation.return_value = QMessageBox.Discard
    dialog.reject()


def test_settings_dialog_confirmation_has_three_choices(
        qt_app: QApplication,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """確認画面が3択で、初期選択とEscは「戻る」になる。"""
    dialog = _SettingsEditDialog()
    dialog.set_data(1)
    dialog.current_data = 2
    dialog.show()

    def check_buttons(message_box: QMessageBox) -> int:
        """表示された確認画面の選択肢と既定動作を検証する。"""
        assert message_box.standardButtons() == (
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
        )
        assert message_box.button(QMessageBox.Save).text() == "保存して閉じる"
        assert message_box.button(QMessageBox.Discard).text() == "破棄"
        assert message_box.button(QMessageBox.Cancel).text() == "戻る"
        assert message_box.defaultButton() == message_box.button(QMessageBox.Cancel)
        assert message_box.escapeButton() == message_box.button(QMessageBox.Cancel)
        return QMessageBox.Cancel

    monkeypatch.setattr(QMessageBox, "exec_", check_buttons)
    dialog.reject()

    assert dialog.isVisible()
    dialog.save_data_mock.assert_not_called()
    dialog.current_data = 1
    dialog.close()


def test_settings_dialog_save_from_close_confirmation(
        qt_app: QApplication,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """閉じる際の「保存して閉じる」でも既存の保存経路を使う。"""
    dialog = _SettingsEditDialog()
    dialog.set_data(1)
    dialog.current_data = 2
    dialog.show()
    monkeypatch.setattr(
        dialog,
        "_confirm_unsaved_changes",
        Mock(return_value=QMessageBox.Save),
    )

    dialog.close()

    dialog.save_data_mock.assert_called_once_with(2)
    assert dialog.has_changes is True
    assert dialog.result() == QDialog.Accepted
    assert not dialog.isVisible()


def test_settings_dialog_save_failure_from_close_confirmation(
        qt_app: QApplication,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """保存失敗時はダイアログを閉じず、変更内容を残す。"""
    dialog = _SettingsEditDialog()
    dialog.set_data(1)
    dialog.current_data = 2
    dialog.save_data_mock.side_effect = ValueError("invalid value")
    dialog.show()
    monkeypatch.setattr(
        dialog,
        "_confirm_unsaved_changes",
        Mock(return_value=QMessageBox.Save),
    )
    critical = Mock()
    monkeypatch.setattr(QMessageBox, "critical", critical)

    dialog.reject()

    dialog.save_data_mock.assert_called_once_with(2)
    critical.assert_called_once()
    assert "invalid value" in critical.call_args.args[2]
    assert dialog.isVisible()
    assert dialog.result() != QDialog.Accepted
    assert not dialog.has_changes
    assert dialog.current_data == 2
    assert dialog.has_unsaved_changes()
    dialog.save_data_mock.side_effect = None
    dialog.close()


def _assert_dialog_confirms_unsaved_changes(
        dialog: AbstractSettingsEditDialog,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """変更済みダイアログの終了時に破棄確認が呼ばれることを確認する。"""
    confirmation = Mock(return_value=QMessageBox.Discard)
    monkeypatch.setattr(dialog, "_confirm_unsaved_changes", confirmation)

    dialog.reject()

    confirmation.assert_called_once_with()


def _assert_dialog_closes_without_confirmation(
        dialog: AbstractSettingsEditDialog,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """未変更のダイアログが破棄確認なしで閉じることを確認する。"""
    confirmation = Mock(return_value=QMessageBox.Discard)
    monkeypatch.setattr(dialog, "_confirm_unsaved_changes", confirmation)

    dialog.reject()

    confirmation.assert_not_called()
    assert dialog.result() == QDialog.Rejected


def _assert_dialog_saves_without_confirmation(
        dialog: AbstractSettingsEditDialog,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """変更済みのダイアログが破棄確認なしで保存されることを確認する。"""
    confirmation = Mock(return_value=QMessageBox.Discard)
    monkeypatch.setattr(dialog, "_confirm_unsaved_changes", confirmation)

    dialog._save()

    confirmation.assert_not_called()
    assert dialog.result() == QDialog.Accepted
    assert dialog.has_changes


def test_project_settings_dialog_confirms_unsaved_changes(
        qt_app: QApplication,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """プロジェクト設定のチェック状態を変えると破棄確認を表示する。"""
    from autoprogen.control.dialog_project_settings import ProjectSettingsEditDialog

    get_usecase = Mock()
    get_usecase.execute.return_value = ProjectSettings.create_default()
    dialog = ProjectSettingsEditDialog(
        catalog=SourceCodeCheckCatalogFactory().create(),
        student_names={},
        project_settings_get_usecase=get_usecase,
        project_settings_put_usecase=Mock(),
    )
    identifier = SourceCodeCheckIdentifier("process", "system")
    rules = dialog._settings_view._rules_widget
    row = rules._rule_ids.index(identifier)
    checkbox = rules._rules_table.item(row, 0)
    checkbox.setCheckState(
        Qt.Unchecked if checkbox.checkState() == Qt.Checked else Qt.Checked
    )

    _assert_dialog_confirms_unsaved_changes(dialog, monkeypatch)


def test_project_settings_dialog_unchanged_close_and_save(
        qt_app: QApplication,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """プロジェクト設定の未変更終了と変更後の保存を確認する。"""
    from autoprogen.control.dialog_project_settings import ProjectSettingsEditDialog

    get_usecase = Mock()
    get_usecase.execute.return_value = ProjectSettings.create_default()
    unchanged = ProjectSettingsEditDialog(
        catalog=SourceCodeCheckCatalogFactory().create(),
        student_names={},
        project_settings_get_usecase=get_usecase,
        project_settings_put_usecase=Mock(),
    )
    _assert_dialog_closes_without_confirmation(unchanged, monkeypatch)

    put_usecase = Mock()
    changed = ProjectSettingsEditDialog(
        catalog=SourceCodeCheckCatalogFactory().create(),
        student_names={},
        project_settings_get_usecase=get_usecase,
        project_settings_put_usecase=put_usecase,
    )
    identifier = SourceCodeCheckIdentifier("process", "system")
    rules = changed._settings_view._rules_widget
    row = rules._rule_ids.index(identifier)
    checkbox = rules._rules_table.item(row, 0)
    checkbox.setCheckState(
        Qt.Unchecked if checkbox.checkState() == Qt.Checked else Qt.Checked
    )
    _assert_dialog_saves_without_confirmation(changed, monkeypatch)
    put_usecase.execute.assert_called_once_with(changed.get_data())


def test_global_settings_dialog_confirms_unsaved_changes(
        qt_app: QApplication,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """グローバル設定の折り返し設定を変えると破棄確認を表示する。"""
    from autoprogen.control.dialog_global_settings import GlobalSettingsEditDialog

    get_usecase = Mock()
    get_usecase.execute.return_value = GlobalSettings.create_default()
    dialog = GlobalSettingsEditDialog(
        compiler_search_usecase=Mock(),
        test_compile_stage_usecase=Mock(),
        global_settings_get_usecase=get_usecase,
        global_settings_put_usecase=Mock(),
    )
    checkbox = dialog._w_settings_edit._w_enable_line_wrap_in_source_code
    checkbox.setChecked(not checkbox.isChecked())

    _assert_dialog_confirms_unsaved_changes(dialog, monkeypatch)


def test_global_settings_dialog_unchanged_close_and_save(
        qt_app: QApplication,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """グローバル設定の未変更終了と変更後の保存を確認する。"""
    from autoprogen.control.dialog_global_settings import GlobalSettingsEditDialog

    get_usecase = Mock()
    get_usecase.execute.return_value = GlobalSettings.create_default()

    def create_dialog(put_usecase: Mock) -> GlobalSettingsEditDialog:
        """共通の既定値を持つグローバル設定ダイアログを生成する。"""
        return GlobalSettingsEditDialog(
            compiler_search_usecase=Mock(),
            test_compile_stage_usecase=Mock(),
            global_settings_get_usecase=get_usecase,
            global_settings_put_usecase=put_usecase,
        )

    unchanged = create_dialog(Mock())
    _assert_dialog_closes_without_confirmation(unchanged, monkeypatch)

    put_usecase = Mock()
    changed = create_dialog(put_usecase)
    checkbox = changed._w_settings_edit._w_enable_line_wrap_in_source_code
    checkbox.setChecked(not checkbox.isChecked())
    monkeypatch.setattr(
        "autoprogen.control.dialog_global_settings.is_compiler_location",
        lambda _: True,
    )
    _assert_dialog_saves_without_confirmation(changed, monkeypatch)
    put_usecase.execute.assert_called_once_with(changed.get_data())


def test_testcase_config_dialog_confirms_unsaved_changes(
        qt_app: QApplication,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """テストケースのタイムアウトを変えると破棄確認を表示する。"""
    from autoprogen.control.dialog_testcase_config_edit import TestCaseConfigEditDialog

    dialog = TestCaseConfigEditDialog(
        data=CaseConfig.create_default(CaseID("case-a")),
        global_settings_get_usecase=Mock(),
        test_test_stage_usecase=Mock(),
    )
    timeout = dialog._w_testcase_edit._w_execute_config_options_edit._sb_timeout
    timeout.setValue(timeout.value() + timeout.singleStep())

    _assert_dialog_confirms_unsaved_changes(dialog, monkeypatch)


def test_testcase_config_dialog_unchanged_close_and_save(
        qt_app: QApplication,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """テストケース設定の未変更終了と変更後の確定を確認する。"""
    from autoprogen.control.dialog_testcase_config_edit import TestCaseConfigEditDialog

    def create_dialog() -> TestCaseConfigEditDialog:
        """同じ既定値を持つテストケース設定ダイアログを生成する。"""
        return TestCaseConfigEditDialog(
            data=CaseConfig.create_default(CaseID("case-a")),
            global_settings_get_usecase=Mock(),
            test_test_stage_usecase=Mock(),
        )

    unchanged = create_dialog()
    _assert_dialog_closes_without_confirmation(unchanged, monkeypatch)

    changed = create_dialog()
    timeout = changed._w_testcase_edit._w_execute_config_options_edit._sb_timeout
    expected_timeout = timeout.value() + timeout.singleStep()
    timeout.setValue(expected_timeout)
    _assert_dialog_saves_without_confirmation(changed, monkeypatch)
    assert changed.get_data().execute_config.options.timeout == expected_timeout


def test_testcase_list_dialog_confirms_unsaved_changes(
        qt_app: QApplication,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """テストケース一覧へ項目を加えると破棄確認を表示する。"""
    from autoprogen.control.dialog_testcase_list_edit import TestCaseListEditDialog

    summary_usecase = Mock()
    summary_usecase.execute.return_value = []
    dialog = TestCaseListEditDialog(
        global_settings_get_usecase=Mock(),
        test_test_stage_usecase=Mock(),
        testcase_list_summary_usecase=summary_usecase,
        testcase_delete_usecase=Mock(),
        testcase_get_usecase=Mock(),
        testcase_put_usecase=Mock(),
    )
    dialog._w_testcase_edit.set_data([
        CaseConfig.create_default(CaseID("case-a")),
    ])

    _assert_dialog_confirms_unsaved_changes(dialog, monkeypatch)


def test_testcase_list_dialog_unchanged_close_and_save(
        qt_app: QApplication,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """テストケース一覧の未変更終了と変更後の保存を確認する。"""
    from autoprogen.control.dialog_testcase_list_edit import TestCaseListEditDialog

    summary_usecase = Mock()
    summary_usecase.execute.return_value = []

    def create_dialog(put_usecase: Mock) -> TestCaseListEditDialog:
        """空のテストケース一覧ダイアログを生成する。"""
        return TestCaseListEditDialog(
            global_settings_get_usecase=Mock(),
            test_test_stage_usecase=Mock(),
            testcase_list_summary_usecase=summary_usecase,
            testcase_delete_usecase=Mock(),
            testcase_get_usecase=Mock(),
            testcase_put_usecase=put_usecase,
        )

    unchanged = create_dialog(Mock())
    _assert_dialog_closes_without_confirmation(unchanged, monkeypatch)

    config = CaseConfig.create_default(CaseID("case-a"))
    put_usecase = Mock()
    changed = create_dialog(put_usecase)
    changed._w_testcase_edit.set_data([config])
    _assert_dialog_saves_without_confirmation(changed, monkeypatch)
    put_usecase.execute.assert_called_once_with(config)
