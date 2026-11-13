"""Phase 2 / Patch C: 学生テーブルとエラー詳細表示の既存契約を固定する。"""

import hashlib
from collections import OrderedDict
from unittest.mock import Mock

import pytest

from autoprogen.control.student_error_detail_parser import (
    SAFETY_ERROR_PREFIX,
    SourceSafetyErrorDetails,
    parse_safety_check_error,
)
from autoprogen.domain.model.stage import (
    BuildStage,
    CompileStage,
    ExecuteStage,
    TestStage as StageTest,
)
from autoprogen.domain.model.stage_path import StagePath
from autoprogen.domain.model.student import Student
from autoprogen.domain.model.student_mark import StudentMark
from autoprogen.domain.model.student_stage_path_result import StudentStagePathResult
from autoprogen.domain.model.student_stage_result import (
    BuildSuccessStudentStageResult,
    CompileFailureStudentStageResult,
    CompileSuccessStudentStageResult,
    ExecuteFailureStudentStageResult,
)
from autoprogen.domain.model.value import StudentID, TestCaseID as CaseID
from autoprogen.usecase.dto.student_table_cell_data import (
    StudentErrorCellData,
    StudentErrorCellDataTextEntry,
    StudentIDCellData,
    StudentNameCellData,
    StudentStageStateCellData,
    StudentStageStateCellDataStageState,
)
from autoprogen.usecase.student_table_load import (
    StudentTableLoadUseCase,
    StudentTableRowSnapshot,
)


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


def _entry(summary: str, detail: str) -> StudentErrorCellDataTextEntry:
    """要約と詳細を指定した表示用データを返す。"""
    return StudentErrorCellDataTextEntry(summary_text=summary, detailed_text=detail)


def _row(entries: list[StudentErrorCellDataTextEntry]) -> StudentTableRowSnapshot:
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
        mark=StudentMark(student_id=STUDENT, score=None),
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


def _stage_path_result(stage_path: StagePath, *results) -> StudentStagePathResult:
    """各ステージの実際の結果モデルから集約を再構成する。"""
    by_stage = {result.stage: result for result in results}
    return StudentStagePathResult(
        student_id=STUDENT,
        stage_results=OrderedDict(
            (stage, by_stage.get(stage)) for stage in stage_path
        ),
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


def test_dialog_exact_message_joining_and_order(qt_app) -> None:
    """要約と詳細の結合規則、空行、複数エラーの順序を全文一致で固定する。"""
    from autoprogen.control.dialog_student_error_detail import StudentErrorDetailDialog

    dialog = StudentErrorDetailDialog(
        student_id=STUDENT,
        error_entries=[
            _entry("最初", "最初\n詳細A"),
            _entry("次", "本文B"),
            _entry("要約のみ", ""),
            _entry("", "詳細のみ"),
            _entry("", ""),
        ],
    )
    try:
        assert dialog.windowTitle() == f"エラーの詳細 - {STUDENT}"
        assert dialog.isModal()
        assert dialog._message_edit.isReadOnly()
        assert dialog._message_edit.toPlainText() == (
            "最初\n詳細A\n\n次\n本文B\n\n要約のみ\n\n詳細のみ"
        )
    finally:
        dialog.close()


def test_dialog_does_not_automatically_deduplicate_equal_entries(qt_app) -> None:
    """詳細ダイアログは受け取った同一メッセージを独自に間引かない。"""
    from autoprogen.control.dialog_student_error_detail import StudentErrorDetailDialog

    item = _entry("同じ失敗", "同じ失敗\n詳細")
    dialog = StudentErrorDetailDialog(student_id=STUDENT, error_entries=[item, item])
    try:
        assert dialog._message_edit.toPlainText() == "同じ失敗\n詳細\n\n同じ失敗\n詳細"
        dialog.set_data([])
        assert dialog._message_edit.toPlainText() == ""
    finally:
        dialog.close()


def test_dialog_close_button_rejects_dialog(qt_app) -> None:
    """閲覧専用のエラー詳細を閉じる操作は従来どおり拒否終了する。"""
    from PyQt5.QtWidgets import QDialog, QDialogButtonBox
    from autoprogen.control.dialog_student_error_detail import StudentErrorDetailDialog

    dialog = StudentErrorDetailDialog(
        student_id=STUDENT,
        error_entries=[_entry("失敗", "失敗")],
    )
    buttons = dialog.findChild(QDialogButtonBox)
    assert buttons is not None
    close_button = buttons.button(QDialogButtonBox.Close)
    assert close_button is not None
    close_button.click()
    assert dialog.result() == QDialog.Rejected
    dialog.close()


def test_table_load_preserves_error_order_and_stage_states() -> None:
    """実際のステージ結果からテストケース順のエラーと状態を構築する。"""
    paths = StagePath.list_paths([CaseID("case_a"), CaseID("case_b")])
    build = BuildSuccessStudentStageResult.create_instance(
        student_id=STUDENT, submission_folder_checksum=123,
    )
    compile_result = CompileSuccessStudentStageResult.create_instance(
        student_id=STUDENT, output="compile output",
    )
    failures = [
        ExecuteFailureStudentStageResult.create_instance(
            student_id=STUDENT, testcase_id=CaseID("case_a"), reason="実行Aが失敗\n原因A",
        ),
        ExecuteFailureStudentStageResult.create_instance(
            student_id=STUDENT, testcase_id=CaseID("case_b"), reason="実行Bが失敗\n原因B",
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
    usecase = StudentTableLoadUseCase(
        student_repo=students,
        stage_path_list_sub_service=path_service,
        student_stage_path_result_repo=repository,
        student_mark_get_sub_service=mark_service,
    )

    row = usecase.execute(progress_callback=lambda _: None)[0]
    assert row.error_cell.text_entries == [
        _entry("実行Aが失敗\n原因A", "実行Aが失敗\n原因A"),
        _entry("実行Bが失敗\n原因B", "実行Bが失敗\n原因B"),
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
    build = BuildSuccessStudentStageResult.create_instance(
        student_id=STUDENT, submission_folder_checksum=123,
    )
    failure = CompileFailureStudentStageResult.create_instance(
        student_id=STUDENT, reason="コンパイルに失敗しました。", output=output,
    )
    students = Mock()
    students.get.return_value = _student()
    path_service = Mock()
    path_service.execute.return_value = [path]
    repository = Mock()
    repository.get.return_value = _stage_path_result(path, build, failure)
    mark_service = Mock()
    mark_service.execute.return_value = StudentMark(student_id=STUDENT, score=None)
    usecase = StudentTableLoadUseCase(
        student_repo=students,
        stage_path_list_sub_service=path_service,
        student_stage_path_result_repo=repository,
        student_mark_get_sub_service=mark_service,
    )

    row = usecase.execute_row(STUDENT)
    assert row.error_cell.text_entries == [
        _entry("コンパイルに失敗しました。", "コンパイルに失敗しました。\n" + output),
    ]


def test_parser_keeps_sorted_detected_lines_from_multiple_errors() -> None:
    """安全性チェックの検出行はエラーをまたいでも重複なし・昇順にまとめる。"""
    source_sha = hashlib.sha256(b"source").hexdigest()
    prefix = SAFETY_ERROR_PREFIX + f"\n検査対象SHA-256: {source_sha}\n"
    entries = [
        _entry(prefix + "8行目: [process.system] 検出\n2行目: [file.read] 検出", ""),
        _entry(prefix + "8行目: [process.system] 検出\n10行目: [file.write] 検出", ""),
    ]
    assert parse_safety_check_error(entries) == SourceSafetyErrorDetails(
        source_sha256=source_sha, line_numbers=(2, 8, 10),
    )


def test_source_safety_widget_already_approved_message(qt_app) -> None:
    """すでに許可済みのソースは再度許可できず、正確な説明文を出す。"""
    from autoprogen.control.widget_source_safety_error import SourceSafetyErrorWidget

    source = "int main(void) { return 0; }\n"
    sha = hashlib.sha256(source.encode("utf-8")).hexdigest()
    widget = SourceSafetyErrorWidget(
        source_code_text=source,
        safety_error=SourceSafetyErrorDetails(sha, (1,)),
        show_editing_symbols=False,
        enable_line_wrap=False,
        already_approved=True,
    )
    try:
        assert widget._status_label.text() == "このソースコードはすでに許可されています。"
        assert not widget._approve_button.isEnabled()
    finally:
        widget.close()
