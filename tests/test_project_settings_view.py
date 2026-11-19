from unittest.mock import Mock

import pytest
from PyQt5.QtWidgets import QMessageBox

from autoprogen.domain.model.project_settings import (
    ProjectSettings,
    SourceCodeCheckIdentifier,
    SourceCodeCheckSkip,
    SourceCodeCheckSuppressions,
)
from autoprogen.domain.model.source_code_check import (
    SourceCodeCheckCatalog,
    SourceCodeCheckEntry,
    SourceCodeCheckGroup,
)
from autoprogen.domain.model.value import StudentID
from autoprogen.domain.service.source_code_check_factory import SourceCodeCheckCatalogFactory
from autoprogen.usecase.project_settings import ProjectSettingsGetUseCase, ProjectSettingsPutUseCase


@pytest.fixture
def qt_app(monkeypatch: pytest.MonkeyPatch):
    """画面を表示しないQtテスト用アプリを用意する。"""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PyQt5.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_project_settings_view_round_trip_and_delete(qt_app) -> None:
    """既存の有効状態と除外情報を復元し、選択行を削除できる。"""
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QAbstractItemView
    from autoprogen.control.widget_project_settings import ProjectSettingsEditWidget

    catalog = SourceCodeCheckCatalogFactory().create()
    existing = ProjectSettings(
        suppressed_source_code_checks=SourceCodeCheckSuppressions({
            SourceCodeCheckIdentifier("process", "system"),
            SourceCodeCheckIdentifier("future_group", "future_rule"),
        }),
        source_code_check_skips=frozenset({
            SourceCodeCheckSkip(StudentID("00A0000000A"), "a" * 64),
            SourceCodeCheckSkip(StudentID("00B0000000B"), "b" * 64),
        }),
        bulk_grading_skips=frozenset({
            StudentID("00A0000000A"),
            StudentID("00B0000000B"),
        }),
    )
    view = ProjectSettingsEditWidget(
        catalog=catalog,
        student_names={
            StudentID("00A0000000A"): "試験 太郎",
            StudentID("00B0000000B"): "試験 花子",
        },
    )
    view.set_data(existing)
    assert view.count() == 3
    assert view.tabText(2) == "一括採点から除外する学生"
    rules = view._rules_widget
    source_skips = view._source_skips_widget
    bulk_skips = view._bulk_skips_widget
    assert rules._rules_table.columnCount() == 3
    assert source_skips._table.columnCount() == 3
    assert rules._rules_table.rowCount() == catalog.entry_count
    assert rules._rules_table.horizontalHeader().isHidden()
    assert rules._rules_table.selectionBehavior() == QAbstractItemView.SelectRows
    assert rules._rules_table.selectionMode() == QAbstractItemView.SingleSelection
    assert not source_skips._table.horizontalHeader().isHidden()
    assert source_skips._table.horizontalHeaderItem(0).text() == "学籍番号"
    assert source_skips._table.horizontalHeaderItem(1).text() == "名前"
    assert source_skips._table.horizontalHeaderItem(2).text() == "ソースコード SHA-256"
    assert source_skips._table.item(0, 0).text() == "00A0000000A"
    assert source_skips._table.item(0, 1).text() == "試験 太郎"
    assert source_skips._table.item(0, 2).text() == "a" * 64
    assert bulk_skips._table.horizontalHeaderItem(0).text() == "学籍番号"
    assert bulk_skips._table.horizontalHeaderItem(1).text() == "名前"
    assert bulk_skips._table.item(0, 0).text() == "00A0000000A"
    assert bulk_skips._table.item(0, 1).text() == "試験 太郎"
    assert not bulk_skips._delete_button.isEnabled()
    first_entry = catalog.groups[0].entries[0]
    assert rules._rules_table.currentRow() == 0
    assert rules._rule_description.text() == first_entry.description
    assert [
        label.text()
        for label in rules._rule_target_labels
    ] == list(first_entry.target_strings)
    assert rules._rule_example.toPlainText() == first_entry.example_source_code
    assert rules._rule_example.minimumHeight() == 250
    assert rules._rule_example.maximumHeight() == 250
    assert view.get_data() == existing

    row = rules._rule_ids.index(SourceCodeCheckIdentifier("process", "system"))
    rules._rules_table.selectRow(row)
    assert rules._rule_description.text() == first_entry.description
    rules._rules_table.item(row, 0).setCheckState(Qt.Checked)
    source_skips._table.selectRow(0)
    assert source_skips._delete_button.isEnabled()
    source_skips._delete_button.click()
    after = view.get_data()
    assert SourceCodeCheckIdentifier("process", "system") not in after.suppressed_source_code_checks
    assert SourceCodeCheckIdentifier("future_group", "future_rule") in after.suppressed_source_code_checks
    assert len(after.source_code_check_skips) == 1
    assert after.bulk_grading_skips == existing.bulk_grading_skips

    bulk_skips._table.selectRow(0)
    assert bulk_skips._delete_button.isEnabled()
    bulk_skips._delete_button.click()
    assert view.get_data().bulk_grading_skips == frozenset({
        StudentID("00B0000000B"),
    })
    view.close()


def test_project_settings_view_reset_replaces_previous_state(qt_app) -> None:
    """set_dataを繰り返しても除外一覧が重複しない。"""
    from autoprogen.control.widget_project_settings import ProjectSettingsEditWidget

    view = ProjectSettingsEditWidget(
        catalog=SourceCodeCheckCatalogFactory().create(),
        student_names={},
    )
    value = ProjectSettings.create_default().with_source_code_check_skip(
        student_id=StudentID("00A0000000A"),
        source_sha256="c" * 64,
    )
    view.set_data(value)
    view.set_data(ProjectSettings.create_default())
    assert view._source_skips_widget._table.rowCount() == 0
    assert view._bulk_skips_widget._table.rowCount() == 0
    assert view.get_data() == ProjectSettings.create_default()
    view.close()


def test_project_settings_view_highlights_example_lines(qt_app) -> None:
    """選択した規則のコード例で検出対象行を黄色く表示する。"""
    from PyQt5.QtGui import QColor
    from autoprogen.control.widget_project_settings import ProjectSettingsEditWidget

    entry = SourceCodeCheckEntry(
        check_id="system",
        name="外部コマンドの実行",
        target_strings=("system",),
        description="外部コマンドの実行を検出します。",
        example_source_code='int main(void) {\n    system("dir");\n}\n',
        example_highlighted_line_numbers=(2,),
    )
    catalog = SourceCodeCheckCatalog(groups=(SourceCodeCheckGroup(
        group_id="process",
        name="プロセス操作",
        entries=(entry,),
    ),))

    view = ProjectSettingsEditWidget(catalog=catalog, student_names={})

    assert view._rules_widget._rule_example.toPlainText() == entry.example_source_code
    selections = view._rules_widget._rule_example.extraSelections()
    assert len(selections) == 1
    assert selections[0].cursor.blockNumber() == 1
    assert selections[0].format.background().color() == QColor("#fff0a6")
    view.close()


def test_project_settings_view_searches_rules_without_changing_settings(qt_app) -> None:
    """検索語に一致する規則だけを表示し、チェック状態は維持する。"""
    from autoprogen.control.widget_project_settings import ProjectSettingsEditWidget

    catalog = SourceCodeCheckCatalogFactory().create()
    view = ProjectSettingsEditWidget(catalog=catalog, student_names={})
    settings_before_search = view.get_data()

    rules = view._rules_widget
    rules._rule_search.setText("process.system")

    visible_rows = [
        row
        for row in range(rules._rules_table.rowCount())
        if not rules._rules_table.isRowHidden(row)
    ]
    assert len(visible_rows) == 1
    visible_row = visible_rows[0]
    assert rules._rule_ids[visible_row] == SourceCodeCheckIdentifier("process", "system")
    assert rules._rules_table.currentRow() == visible_row
    assert view.get_data() == settings_before_search

    rules._rule_search.clear()
    assert all(
        not rules._rules_table.isRowHidden(row)
        for row in range(rules._rules_table.rowCount())
    )
    view.close()


def test_project_settings_dialog_saves_only_on_save(
        qt_app,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """キャンセルでは保存せず、保存後のみRepositoryへの更新が発生する。"""
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QDialog
    from autoprogen.control.dialog_project_settings import ProjectSettingsEditDialog

    settings = ProjectSettings.create_default()
    repository = Mock()
    repository.get.return_value = settings
    get_usecase = ProjectSettingsGetUseCase(project_settings_repo=repository)
    put_usecase = ProjectSettingsPutUseCase(
        project_settings_repo=repository,
        student_change_event_bus=Mock(),
    )
    catalog = SourceCodeCheckCatalogFactory().create()

    dialog = ProjectSettingsEditDialog(
        catalog=catalog,
        student_names={},
        project_settings_get_usecase=get_usecase,
        project_settings_put_usecase=put_usecase,
    )
    rules = dialog._settings_view._rules_widget
    row = rules._rule_ids.index(SourceCodeCheckIdentifier("process", "system"))
    checkbox = rules._rules_table.item(row, 0)
    checkbox.setCheckState(Qt.Unchecked if checkbox.checkState() == Qt.Checked else Qt.Checked)
    monkeypatch.setattr(dialog, "_confirm_unsaved_changes", Mock(return_value=QMessageBox.Discard))
    dialog.reject()
    repository.put.assert_not_called()

    dialog2 = ProjectSettingsEditDialog(
        catalog=catalog,
        student_names={},
        project_settings_get_usecase=get_usecase,
        project_settings_put_usecase=put_usecase,
    )
    checkbox2 = dialog2._settings_view._rules_widget._rules_table.item(row, 0)
    checkbox2.setCheckState(Qt.Unchecked if checkbox2.checkState() == Qt.Checked else Qt.Checked)
    dialog2._save()
    assert dialog2.result() == QDialog.Accepted
    repository.put.assert_called_once()
    assert repository.put.call_args.args[0] != settings
    assert dialog2.has_changes is True
    dialog.close()
    dialog2.close()


def test_new_project_defaults_suppress_file_and_common_c_rules() -> None:
    """一般的なファイル入出力とメモリ操作だけを初期状態で抑制する。"""
    settings = ProjectSettings.create_default()
    assert SourceCodeCheckIdentifier("file", "open") in settings.suppressed_source_code_checks
    assert SourceCodeCheckIdentifier("file", "read") in settings.suppressed_source_code_checks
    assert SourceCodeCheckIdentifier("file", "write") in settings.suppressed_source_code_checks
    assert SourceCodeCheckIdentifier("common_c", "malloc") in settings.suppressed_source_code_checks
    assert SourceCodeCheckIdentifier("common_c", "free") in settings.suppressed_source_code_checks
    assert SourceCodeCheckIdentifier("file", "delete") not in settings.suppressed_source_code_checks
    assert SourceCodeCheckIdentifier("process", "system") not in settings.suppressed_source_code_checks


def test_default_suppressed_ids_are_in_catalog() -> None:
    """標準設定で抑制する規則が実際のカタログに存在する。"""
    catalog = SourceCodeCheckCatalogFactory().create()
    known = {
        SourceCodeCheckIdentifier(group.group_id, entry.check_id)
        for group in catalog.groups
        for entry in group.entries
    }
    assert set(ProjectSettings.create_default().suppressed_source_code_checks) <= known


def test_project_settings_dialog_canceled_delete_is_not_saved(
        qt_app,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """除外ハッシュの削除は、キャンセルした場合に永続化されない。"""
    from autoprogen.control.dialog_project_settings import ProjectSettingsEditDialog
    settings = ProjectSettings.create_default().with_source_code_check_skip(
        student_id=StudentID("00A0000000A"),
        source_sha256="d" * 64,
    )
    repository = Mock()
    repository.get.return_value = settings
    dialog = ProjectSettingsEditDialog(
        catalog=SourceCodeCheckCatalogFactory().create(),
        student_names={},
        project_settings_get_usecase=ProjectSettingsGetUseCase(project_settings_repo=repository),
        project_settings_put_usecase=ProjectSettingsPutUseCase(
            project_settings_repo=repository,
            student_change_event_bus=Mock(),
        ),
    )
    dialog._settings_view._source_skips_widget._table.selectRow(0)
    dialog._settings_view._source_skips_widget._delete_button.click()
    assert not dialog._settings_view.get_data().source_code_check_skips
    monkeypatch.setattr(dialog, "_confirm_unsaved_changes", Mock(return_value=QMessageBox.Discard))
    dialog.reject()
    repository.put.assert_not_called()
    dialog.close()


def test_project_settings_dialog_canceled_bulk_skip_delete_is_not_saved(
        qt_app,
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    """採点除外の削除はキャンセルした場合に永続化されない。"""
    from autoprogen.control.dialog_project_settings import ProjectSettingsEditDialog

    student_id = StudentID("00A0000000A")
    settings = ProjectSettings.create_default().with_bulk_grading_skip(student_id)
    repository = Mock()
    repository.get.return_value = settings
    dialog = ProjectSettingsEditDialog(
        catalog=SourceCodeCheckCatalogFactory().create(),
        student_names={student_id: "試験 太郎"},
        project_settings_get_usecase=ProjectSettingsGetUseCase(
            project_settings_repo=repository,
        ),
        project_settings_put_usecase=ProjectSettingsPutUseCase(
            project_settings_repo=repository,
            student_change_event_bus=Mock(),
        ),
    )
    dialog._settings_view._bulk_skips_widget._table.selectRow(0)
    dialog._settings_view._bulk_skips_widget._delete_button.click()
    assert not dialog._settings_view.get_data().bulk_grading_skips

    monkeypatch.setattr(
        dialog,
        "_confirm_unsaved_changes",
        Mock(return_value=QMessageBox.Discard),
    )
    dialog.reject()

    repository.put.assert_not_called()
    dialog.close()


def test_project_settings_dialog_saves_bulk_skip_delete(qt_app) -> None:
    """採点除外の削除は保存操作を行った場合だけ永続化する。"""
    from autoprogen.control.dialog_project_settings import ProjectSettingsEditDialog

    student_id = StudentID("00A0000000A")
    settings = ProjectSettings.create_default().with_bulk_grading_skip(student_id)
    repository = Mock()
    repository.get.return_value = settings
    dialog = ProjectSettingsEditDialog(
        catalog=SourceCodeCheckCatalogFactory().create(),
        student_names={student_id: "試験 太郎"},
        project_settings_get_usecase=ProjectSettingsGetUseCase(
            project_settings_repo=repository,
        ),
        project_settings_put_usecase=ProjectSettingsPutUseCase(
            project_settings_repo=repository,
            student_change_event_bus=Mock(),
        ),
    )
    dialog._settings_view._bulk_skips_widget._table.selectRow(0)
    dialog._settings_view._bulk_skips_widget._delete_button.click()

    dialog._save()

    saved = repository.put.call_args.args[0]
    assert saved.bulk_grading_skips == frozenset()
    assert saved.suppressed_source_code_checks == settings.suppressed_source_code_checks
    assert saved.source_code_check_skips == settings.source_code_check_skips
    dialog.close()
