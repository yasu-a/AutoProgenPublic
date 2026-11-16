"""学生テーブルとエラー詳細表示の既存契約を固定する。"""

import hashlib
from collections import OrderedDict
from datetime import datetime
from unittest.mock import Mock

import pytest

from autoprogen.domain.error.stage.base import StageError
from autoprogen.domain.error.stage.compile import CompilerNotConfiguredError, SourceSafetyViolationError
from autoprogen.domain.error.stage.execute import ExecutableNotFoundError, ExecutionTimeoutError
from autoprogen.domain.model.stage import (
    BuildStage,
    CompileStage,
    ExecuteStage,
    TestStage as StageTest,
)
from autoprogen.domain.model.stage_path import StagePath
from autoprogen.domain.model.student import Student
from autoprogen.domain.model.student_mark import StudentMark
from autoprogen.domain.model.source_code import SourceCode
from autoprogen.domain.model.source_code_check import SourceCodeCheckFinding
from autoprogen.domain.model.project_settings import SourceCodeCheckSuppressions
from autoprogen.domain.model.student_stage_path_result import StudentStagePathResult
from autoprogen.domain.model.student_stage_result import (
    BuildStudentStageResult,
    CompileStudentStageResult,
    ExecuteStudentStageResult,
)
from autoprogen.domain.model.value import StudentID, TestCaseID as CaseID
from autoprogen.domain.service.source_code_check_factory import SourceCodeCheckCatalogFactory
from autoprogen.service.stage_error_text import StageErrorTextFormatter
from autoprogen.usecase.dto.student_table_cell_data import (
    StudentErrorCellData,
    StudentErrorCellDataTextEntry,
    StudentIDCellData,
    StudentNameCellData,
    StudentStageStateCellData,
    StudentStageStateCellDataStageState,
)
from autoprogen.usecase.main_window import MainWindowFacade, StudentTableRowSnapshot


STUDENT = StudentID("21D5109047B")


@pytest.fixture
def qt_app(monkeypatch: pytest.MonkeyPatch):
    """既存のGUIテストと同様、画面を表示せずにQtを初期化する。"""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PyQt5.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _entry(
        summary: str,
        detail: str,
        error: StageError | None = None,
) -> StudentErrorCellDataTextEntry:
    """要約と詳細を指定した表示用データを返す。"""
    return StudentErrorCellDataTextEntry(
        summary_text=summary,
        detailed_text=detail,
        error=error,
    )


def _row(
        entries: list[StudentErrorCellDataTextEntry],
        *,
        mark: StudentMark | None = None,
) -> StudentTableRowSnapshot:
    """エラー表示以外の欄を固定した学生テーブルの一行を構築する。"""
    return StudentTableRowSnapshot(
        student_id=STUDENT,
        id_cell=StudentIDCellData(STUDENT, str(STUDENT), True),
        name_cell=StudentNameCellData(STUDENT, "試験 太郎"),
        stage_cells={
            stage_type: StudentStageStateCellData(STUDENT, stage_type, {})
            for stage_type in (BuildStage, CompileStage, ExecuteStage, StageTest)
        },
        error_cell=StudentErrorCellData(STUDENT, entries),
        mark=mark or StudentMark(student_id=STUDENT, score=None),
    )


def _student() -> Student:
    """全件ロードと一行ロードの両方で使用する学生情報を返す。"""
    return Student(
        student_id=STUDENT,
        name="試験 太郎",
        name_en="Test Taro",
        email_address="test@example.com",
        submitted_at=None,
        num_submissions=1,
        submission_folder_name="submitted",
    )


def _table_facade(
        *,
        student_repository: Mock,
        stage_path_list_sub_service: Mock,
        student_stage_path_result_repository: Mock,
        student_mark_get_sub_service: Mock,
) -> MainWindowFacade:
    """エラー表示用の学生行を構築するFacadeを返す。"""
    return MainWindowFacade(
        current_project_repository=Mock(),
        student_folder_show_in_explorer_io=Mock(),
        student_repository=student_repository,
        stage_path_list_sub_service=stage_path_list_sub_service,
        student_stage_path_result_repository=student_stage_path_result_repository,
        student_mark_get_sub_service=student_mark_get_sub_service,
        stage_error_text_formatter=_formatter(),
        student_mark_get_usecase=Mock(),
        student_mark_put_usecase=Mock(),
        student_list_id_usecase=Mock(),
        student_run_next_stage_usecase=Mock(),
        student_stage_result_clear_service=Mock(),
        app_version_repository=Mock(),
        resource_usage_io=Mock(),
        student_change_event_bus=Mock(),
        task_manager=Mock(),
    )


def _stage_path_result(stage_path: StagePath, *results) -> StudentStagePathResult:
    """各ステージの実際の結果モデルから集約を再構成する。"""
    by_stage = {result.stage: result for result in results}
    return StudentStagePathResult(
        student_id=STUDENT,
        stage_results=OrderedDict(
            (stage, by_stage.get(stage)) for stage in stage_path
        ),
    )


def _formatter() -> StageErrorTextFormatter:
    """本番カタログを使う表示用フォーマッタを返す。"""
    return StageErrorTextFormatter(
        source_code_check_catalog_factory=SourceCodeCheckCatalogFactory(),
    )


def test_duplicate_summaries_keep_first_detail_and_original_order() -> None:
    """同じ要約は先に現れた詳細だけを残し、異なる要約は出現順に保つ。"""
    entries = [
        _entry("A", "Aの詳細・最初"),
        _entry("B", "Bの詳細"),
        _entry("A", "Aの詳細・二番目"),
        _entry("C", "Cの詳細"),
    ]
    cell = StudentErrorCellData(STUDENT, entries)
    assert cell.aggregate_text_entries() == [entries[0], entries[1], entries[3]]
    assert cell.text_entries == entries


def test_exact_duplicate_details_are_removed_for_detail_dialog() -> None:
    """詳細画面では完全一致だけを除き、同じ概要を持つ異なる詳細は残す。"""
    entries = [
        _entry("安全性チェック", "1行目: system"),
        _entry("安全性チェック", "1行目: system"),
        _entry("安全性チェック", "2行目: fopen"),
    ]
    cell = StudentErrorCellData(STUDENT, entries)

    assert cell.distinct_text_entries() == [entries[0], entries[2]]


@pytest.mark.parametrize(
    ("entries", "display", "tooltip"),
    [
        ([], "", ""),
        ([_entry("コンパイル失敗", "コンパイル失敗\nMSVCの出力")],
         "コンパイル失敗", "◆ コンパイル失敗\nMSVCの出力"),
        ([_entry("A", "詳細A"), _entry("A", "上書きされない詳細"), _entry("B", "詳細B")],
         "A（他1件のエラー）", "◆ 詳細A\n◆ 詳細B"),
    ],
)
def test_table_error_cell_exact_display_and_tooltip(
        qt_app, entries, display: str, tooltip: str,
) -> None:
    """学生テーブルのエラー欄は要約・件数・ツールチップの全文を維持する。"""
    from PyQt5.QtCore import Qt
    from autoprogen.control.widget_student_table import (
        StudentTableColumns,
        StudentTableModelDataProvider,
    )

    provider = StudentTableModelDataProvider(student_ids=[STUDENT])
    provider.set_rows([_row(entries)])
    assert provider.get_data(0, StudentTableColumns.COL_ERROR, Qt.DisplayRole) == display
    assert provider.get_data(0, StudentTableColumns.COL_ERROR, Qt.ToolTipRole) == tooltip
    assert provider.get_data(0, StudentTableColumns.COL_ERROR, Qt.DecorationRole) is None


def test_table_error_cell_cache_is_invalidated_on_row_update(qt_app) -> None:
    """エラーが解消・変更された場合は古い表示と詳細を再利用しない。"""
    from PyQt5.QtCore import Qt
    from autoprogen.control.widget_student_table import (
        CachedStudentTableModelDataProvider,
        StudentTableColumns,
        StudentTableModelDataProvider,
    )

    provider = CachedStudentTableModelDataProvider.from_provider(
        StudentTableModelDataProvider(student_ids=[STUDENT]),
    )
    provider.set_rows([_row([_entry("古い失敗", "古い詳細")])])
    col = StudentTableColumns.COL_ERROR
    assert provider.get_data(0, col, Qt.DisplayRole) == "古い失敗"
    assert provider.get_data(0, col, Qt.ToolTipRole) == "◆ 古い詳細"

    provider.replace_row(0, _row([_entry("新しい失敗", "新しい詳細")]))
    assert provider.get_data(0, col, Qt.DisplayRole) == "新しい失敗"
    assert provider.get_data(0, col, Qt.ToolTipRole) == "◆ 新しい詳細"

    provider.replace_row(0, _row([]))
    assert provider.get_data(0, col, Qt.DisplayRole) == ""
    assert provider.get_data(0, col, Qt.ToolTipRole) == ""


def test_table_confirmed_row_has_distinct_background(qt_app) -> None:
    """確定済みの行だけに背景色を付け、行更新時に表示を戻す。"""
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QColor
    from autoprogen.control.widget_student_table import (
        CachedStudentTableModelDataProvider,
        StudentTableColumns,
        StudentTableModelDataProvider,
    )

    provider = CachedStudentTableModelDataProvider.from_provider(
        StudentTableModelDataProvider(student_ids=[STUDENT]),
    )
    provider.set_rows([
        _row([], mark=StudentMark(STUDENT, 80, confirmed=True)),
    ])

    for column in range(len(StudentTableColumns.HEADER)):
        assert provider.get_data(0, column, Qt.BackgroundRole) == QColor("#dffe8b")

    provider.replace_row(
        0,
        _row([], mark=StudentMark(STUDENT, 80, confirmed=False)),
    )

    for column in range(len(StudentTableColumns.HEADER)):
        assert provider.get_data(0, column, Qt.BackgroundRole) is None


def test_detail_widget_exact_message_joining_and_order(qt_app) -> None:
    """要約と詳細の結合規則、空行、複数エラーの順序を全文一致で固定する。"""
    from autoprogen.control.widget_student_error_detail import StudentErrorDetailWidget

    widget = StudentErrorDetailWidget(
        error_entries=[
            _entry("最初", "最初\n詳細A"),
            _entry("次", "本文B"),
            _entry("要約のみ", ""),
            _entry("", "詳細のみ"),
            _entry("", ""),
        ],
    )
    try:
        assert widget._message_edit.isReadOnly()
        assert widget._message_edit.toPlainText() == (
            "最初\n詳細A\n\n次\n本文B\n\n要約のみ\n\n詳細のみ"
        )
    finally:
        widget.close()


def test_detail_widget_does_not_automatically_deduplicate_equal_entries(qt_app) -> None:
    """詳細Widgetは受け取った同一メッセージを独自に間引かない。"""
    from autoprogen.control.widget_student_error_detail import StudentErrorDetailWidget

    item = _entry("同じ失敗", "同じ失敗\n詳細")
    widget = StudentErrorDetailWidget(error_entries=[item, item])
    try:
        assert widget._message_edit.toPlainText() == "同じ失敗\n詳細\n\n同じ失敗\n詳細"
        widget.set_data([])
        assert widget._message_edit.toPlainText() == ""
    finally:
        widget.close()


def test_error_detail_widget_uses_horizontal_layout(qt_app) -> None:
    """下部ドックでは詳細と追加Widgetを横方向に配置する。"""
    from PyQt5.QtCore import Qt
    from autoprogen.control.widget_student_error_detail import StudentErrorDetailWidget

    widget = StudentErrorDetailWidget(
        error_entries=[_entry("エラー", "詳細")],
    )
    try:
        assert widget._splitter.orientation() == Qt.Horizontal
    finally:
        widget.close()


def test_table_load_preserves_error_order_and_stage_states() -> None:
    """実際のステージ結果からテストケース順のエラーと状態を構築する。"""
    paths = StagePath.list_paths([CaseID("case_a"), CaseID("case_b")])
    build = BuildStudentStageResult.create_instance(
        student_id=STUDENT, submission_folder_checksum=123, error=None,
    )
    compile_result = CompileStudentStageResult.create_instance(
        student_id=STUDENT,
        output="compile output",
        suppressed_source_code_checks=SourceCodeCheckSuppressions(),
        source_code_check_skipped=False,
        error=None,
    )
    failures = [
        ExecuteStudentStageResult.create_instance(
            student_id=STUDENT,
            testcase_id=CaseID("case_a"),
            execute_config_mtime=datetime(2026, 1, 1),
            output_file_collection=None,
            error=ExecutableNotFoundError(),
        ),
        ExecuteStudentStageResult.create_instance(
            student_id=STUDENT,
            testcase_id=CaseID("case_b"),
            execute_config_mtime=datetime(2026, 1, 1),
            output_file_collection=None,
            error=ExecutionTimeoutError(),
        ),
    ]
    stage_results = [
        _stage_path_result(path, build, compile_result, failure)
        for path, failure in zip(paths, failures)
    ]
    students = Mock()
    students.list.return_value = [_student()]
    students.get.return_value = _student()
    path_service = Mock()
    path_service.execute.return_value = paths
    repository = Mock()
    repository.get.side_effect = stage_results
    mark_service = Mock()
    mark_service.execute.return_value = StudentMark(student_id=STUDENT, score=None)
    facade = _table_facade(
        student_repository=students,
        stage_path_list_sub_service=path_service,
        student_stage_path_result_repository=repository,
        student_mark_get_sub_service=mark_service,
    )

    row = facade.load_student_table(progress_callback=lambda _: None)[0]
    assert row.error_cell.text_entries == [
        _entry(
            "実行対象が存在しません",
            "実行対象が存在しません",
            failures[0].error,
        ),
        _entry(
            "実行がタイムアウトしました\n"
            "この環境のスペックに対して並列タスク数が多すぎる・"
            "プログラムが入力を待っている・無限ループしているなどの可能性があります",
            "実行がタイムアウトしました\n"
            "この環境のスペックに対して並列タスク数が多すぎる・"
            "プログラムが入力を待っている・無限ループしているなどの可能性があります",
            failures[1].error,
        ),
    ]
    state = StudentStageStateCellDataStageState
    assert list(row.stage_cells[BuildStage].states.values()) == [
        state.FINISHED_SUCCESS, state.FINISHED_SUCCESS,
    ]
    assert list(row.stage_cells[ExecuteStage].states.values()) == [
        state.FINISHED_FAILURE, state.FINISHED_FAILURE,
    ]
    assert list(row.stage_cells[StageTest].states.values()) == [
        state.UNFINISHED, state.UNFINISHED,
    ]
    assert repository.get.call_count == 2


@pytest.mark.parametrize("output", ["", "main.c(5): error C2143\n"])
def test_table_load_preserves_compile_output_in_detail(output: str) -> None:
    """COMPILE失敗の外部出力と末尾改行を詳細文から落とさない。"""
    path = StagePath.list_paths([CaseID("case_a")])[0]
    build = BuildStudentStageResult.create_instance(
        student_id=STUDENT, submission_folder_checksum=123, error=None,
    )
    failure = CompileStudentStageResult.create_instance(
        student_id=STUDENT,
        error=CompilerNotConfiguredError(),
        output=output,
        suppressed_source_code_checks=SourceCodeCheckSuppressions(),
        source_code_check_skipped=False,
    )
    students = Mock()
    students.get.return_value = _student()
    path_service = Mock()
    path_service.execute.return_value = [path]
    repository = Mock()
    repository.get.return_value = _stage_path_result(path, build, failure)
    mark_service = Mock()
    mark_service.execute.return_value = StudentMark(student_id=STUDENT, score=None)
    facade = _table_facade(
        student_repository=students,
        stage_path_list_sub_service=path_service,
        student_stage_path_result_repository=repository,
        student_mark_get_sub_service=mark_service,
    )

    row = facade.load_student_table_row(STUDENT)
    assert row.error_cell.text_entries == [
        _entry(
            "コンパイルに失敗しました。\nコンパイラが設定されていません",
            "コンパイルに失敗しました。\nコンパイラが設定されていません\n" + output,
            failure.error,
        ),
    ]


def test_safety_error_display_limits_findings_and_uses_current_rule_name() -> None:
    """安全性チェック表示は現在の規則名を使い、51件目以降を件数表示へまとめる。"""
    error = SourceSafetyViolationError(
        source_sha256="a" * 64,
        findings=tuple(
            SourceCodeCheckFinding(
                line_number=line_number,
                group_id="process",
                check_id="system",
            )
            for line_number in range(1, 52)
        ),
    )
    text = _formatter().format_summary(error)
    assert "1行目: [process.system] 外部コマンドの実行" in text
    assert "50行目: [process.system] 外部コマンドの実行" in text
    assert "51行目:" not in text
    assert text.endswith("ほか1件の検出があります。")


def test_widget_keeps_sorted_detected_lines_from_multiple_errors(qt_app) -> None:
    """安全性チェックの検出行は構造化エラーから重複なし・昇順にまとめる。"""
    from autoprogen.control.widget_source_safety_error import SourceSafetyErrorWidget

    source_sha = hashlib.sha256(b"source").hexdigest()
    errors = [
        SourceSafetyViolationError(
            source_sha256=source_sha,
            findings=(
                SourceCodeCheckFinding(8, "process", "system"),
                SourceCodeCheckFinding(2, "file", "read"),
            ),
        ),
        SourceSafetyViolationError(
            source_sha256=source_sha,
            findings=(
                SourceCodeCheckFinding(8, "process", "system"),
                SourceCodeCheckFinding(10, "file", "write"),
            ),
        ),
    ]
    widget = SourceSafetyErrorWidget(
        source_code=SourceCode(text="\n" * 10),
        safety_errors=errors,
        show_editing_symbols=False,
        enable_line_wrap=False,
    )
    try:
        selections = widget._source_view.extraSelections()
        assert [selection.cursor.blockNumber() + 1 for selection in selections] == [2, 8, 10]
    finally:
        widget.close()


def test_source_safety_widget_already_approved_message(qt_app) -> None:
    """すでに許可済みのソースは再度許可できず、正確な説明文を出す。"""
    from autoprogen.control.widget_source_safety_error import SourceSafetyErrorWidget

    source = "int main(void) { return 0; }\n"
    sha = hashlib.sha256(source.encode("utf-8")).hexdigest()
    widget = SourceSafetyErrorWidget(
        source_code=SourceCode(text=source),
        safety_errors=(SourceSafetyViolationError(
            source_sha256=sha,
            findings=(SourceCodeCheckFinding(1, "process", "system"),),
        ),),
        show_editing_symbols=False,
        enable_line_wrap=False,
        already_approved=True,
    )
    try:
        assert widget._status_label.text() == "このソースコードはすでに許可されています。"
        assert not widget._approve_button.isEnabled()
    finally:
        widget.close()
