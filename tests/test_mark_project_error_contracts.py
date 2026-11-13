"""採点画面とプロジェクト操作のエラー表示契約を固定する。"""

from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest

from autoprogen.domain.error import (
    ManabaReportArchiveError,
    ManabaReportListArchiveValidateServiceError,
    ManabaReportListParserError,
    ReadonlyExcelWorksheetGatewayError,
    StudentMasterServiceError,
    StudentSubmissionServiceError,
)
from autoprogen.domain.model.expected_output_file import ExpectedOutputFile
from autoprogen.domain.model.output_file import OutputFileCollection
from autoprogen.domain.model.stage import TestStage as StageTest
from autoprogen.domain.model.stage_path import StagePath
from autoprogen.domain.model.student import Student
from autoprogen.domain.model.student_mark import StudentMark
from autoprogen.domain.model.student_stage_path_result import StudentStagePathResult
from autoprogen.domain.model.student_stage_result import (
    BuildSuccessStudentStageResult,
    CompileFailureStudentStageResult,
    CompileSuccessStudentStageResult,
    ExecuteSuccessStudentStageResult,
    TestResultOutputFileCollection as StageTestResultCollection,
    TestSuccessStudentStageResult as StageTestSuccess,
)
from autoprogen.domain.model.test_result_output_file_entry import (
    TestResultAbsentOutputFileEntry as AbsentOutputEntry,
)
from autoprogen.domain.model.value import (
    FileID,
    ProjectID,
    StudentID,
    TargetID,
    TestCaseID as CaseID,
)
from autoprogen.service.dto.project import ProjectConfigState
from autoprogen.usecase.current_project import CurrentProjectInitializeStaticUseCase
from autoprogen.usecase.dto.student_mark_view_data import (
    StudentMarkState,
    StudentTestCaseSummaryState,
)
from autoprogen.usecase.project import ProjectListRecentSummaryUseCase
from autoprogen.usecase.student_mark_view_data import (
    StudentMarkViewDataGetMarkSummaryUseCase,
    StudentMarkViewDataGetTestResultUseCase,
)


STUDENT = StudentID("21D5109047B")
CASE = CaseID("case_a")
MTIME = datetime(2026, 11, 13, 14, 30, 0)


@pytest.fixture
def qt_app(monkeypatch: pytest.MonkeyPatch):
    """採点画面のウィジェットを画面表示なしで検証できるようにする。"""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PyQt5.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _student() -> Student:
    """採点画面向けの最低限の学生情報を作る。"""
    return Student(
        student_id=STUDENT,
        name="試験 太郎",
        name_en="Test Taro",
        email_address="test@example.com",
        submitted_at=None,
        num_submissions=1,
        submission_folder_name="submitted",
    )


def _result_collection(*, accepted: bool) -> StageTestResultCollection:
    """正解は空の出力期待、誤答は必要な出力欠落で表現する。"""
    if accepted:
        return StageTestResultCollection()
    return StageTestResultCollection([
        AbsentOutputEntry(
            file_id=FileID.STDOUT,
            expected=ExpectedOutputFile.create_default(FileID.STDOUT),
        ),
    ])


def _stage_result(*results) -> StudentStagePathResult:
    """全処理済み／途中失敗／未実行の3状態を同じ実モデルで表す。"""
    path = StagePath.list_paths([CASE])[0]
    by_stage = {result.stage: result for result in results}
    return StudentStagePathResult(
        student_id=STUDENT,
        stage_results=OrderedDict((stage, by_stage.get(stage)) for stage in path),
    )


def _build_success() -> BuildSuccessStudentStageResult:
    """共有BUILDが正常終了した結果を作る。"""
    return BuildSuccessStudentStageResult.create_instance(
        student_id=STUDENT, submission_folder_checksum=7,
    )


def _compile_success() -> CompileSuccessStudentStageResult:
    """共有COMPILEが正常終了した結果を作る。"""
    return CompileSuccessStudentStageResult.create_instance(
        student_id=STUDENT, output="compiler output",
    )


def _execute_success() -> ExecuteSuccessStudentStageResult:
    """EXECUTEが正常終了した結果を作る。"""
    return ExecuteSuccessStudentStageResult.create_instance(
        student_id=STUDENT,
        testcase_id=CASE,
        execute_config_mtime=MTIME,
        output_file_collection=OutputFileCollection(),
    )


def _mark_testcase_usecase(stage_result: StudentStagePathResult):
    """採点画面の取得処理に実際のステージ結果を渡す。"""
    path_service = Mock()
    path_service.execute.return_value = stage_result.stage_path
    stage_service = Mock()
    stage_service.execute.return_value = stage_result
    return StudentMarkViewDataGetTestResultUseCase(
        stage_path_get_by_testcase_id_service=path_service,
        student_stage_path_result_get_service=stage_service,
    )


def test_marking_screen_uses_compiler_output_as_untestable_reason() -> None:
    """採点画面にはCOMPILE失敗理由とコンパイラ出力を改行込みで表示する。"""
    result = _stage_result(
        _build_success(),
        CompileFailureStudentStageResult.create_instance(
            student_id=STUDENT,
            reason="コンパイルに失敗しました。",
            output="main.c(5): error C2143\n",
        ),
    )
    view = _mark_testcase_usecase(result).execute(STUDENT, CASE)
    assert view.state is StudentTestCaseSummaryState.UNTESTABLE
    assert view.title_text == "テストできません"
    assert not view.is_success
    assert view.detailed_reason == "コンパイルに失敗しました。\nmain.c(5): error C2143\n"
    with pytest.raises(ValueError, match="output and results not provided"):
        _ = view.output_and_results


def test_marking_screen_uses_unfinished_fallback() -> None:
    """実行開始前は具体的な失敗理由ではなく既存の未完了メッセージを使う。"""
    view = _mark_testcase_usecase(_stage_result()).execute(STUDENT, CASE)
    assert view.state is StudentTestCaseSummaryState.UNTESTABLE
    assert view.detailed_reason == "処理が未完了です"
    assert not view.is_success


@pytest.mark.parametrize("accepted", [True, False])
def test_marking_screen_distinguishes_accepted_and_wrong_answer(accepted: bool) -> None:
    """不正解もTESTステージの成功結果であり、テスト不可とは区別される。"""
    collection = _result_collection(accepted=accepted)
    result = _stage_result(
        _build_success(),
        _compile_success(),
        _execute_success(),
        StageTestSuccess.create_instance(
            student_id=STUDENT,
            testcase_id=CASE,
            test_config_mtime=MTIME,
            test_result_output_file_collection=collection,
        ),
    )
    view = _mark_testcase_usecase(result).execute(STUDENT, CASE)
    assert view.is_success
    assert view.output_and_results is collection
    if accepted:
        assert view.state is StudentTestCaseSummaryState.ACCEPTED
        assert view.title_text == "正解です"
    else:
        assert view.state is StudentTestCaseSummaryState.WRONG_ANSWER
        assert view.title_text == "正解条件を満たしていません"
    with pytest.raises(ValueError, match="detailed reason not provided"):
        _ = view.detailed_reason


@pytest.mark.parametrize(
    ("accepted", "abbreviation", "title"),
    [
        (True, "AC", "正解です"),
        (False, "WA", "正解条件を満たしていません"),
    ],
)
def test_marking_testcase_indicator_exact_labels(
        qt_app, accepted: bool, abbreviation: str, title: str,
) -> None:
    """採点画面の正解・不正解表示とインジケータの略号を固定する。"""
    from autoprogen.control.widget_testcase_test_result_list import (
        TestCaseTestResultListItemWidget as ResultItemWidget,
    )

    collection = _result_collection(accepted=accepted)
    result = _stage_result(
        _build_success(), _compile_success(), _execute_success(),
        StageTestSuccess.create_instance(
            student_id=STUDENT,
            testcase_id=CASE,
            test_config_mtime=MTIME,
            test_result_output_file_collection=collection,
        ),
    )
    view = _mark_testcase_usecase(result).execute(STUDENT, CASE)
    widget = ResultItemWidget()
    try:
        widget.set_data(view)
        assert widget._l_testcase_name.text() == str(CASE)
        assert widget._l_detail.text() == title
        assert widget._l_indicator._l_text.text() == abbreviation
        assert widget._l_indicator.toolTip() == title
    finally:
        widget.close()


def test_marking_untestable_indicator_exact_label(qt_app) -> None:
    """テスト不可は不正解WAではなくEとして表示される。"""
    from autoprogen.control.widget_testcase_test_result_list import (
        TestCaseTestResultListItemWidget as ResultItemWidget,
    )

    view = _mark_testcase_usecase(_stage_result()).execute(STUDENT, CASE)
    widget = ResultItemWidget()
    try:
        widget.set_data(view)
        assert widget._l_detail.text() == "テストできません"
        assert widget._l_indicator._l_text.text() == "E"
        assert widget._l_indicator.toolTip() == "テストできません"
    finally:
        widget.close()


@pytest.mark.parametrize(
    ("has_testcase", "rollback_needed", "expected_state", "expected_reason"),
    [
        (False, False, StudentMarkState.NO_TEST_FOUND, "テストケースがありません"),
        (True, False, StudentMarkState.READY, None),
        (True, True, StudentMarkState.RERUN_REQUIRED, "変更が検出されたため再実行が必要です"),
    ],
)
def test_marking_summary_status_is_not_a_stage_error(
        has_testcase: bool,
        rollback_needed: bool,
        expected_state: StudentMarkState,
        expected_reason: str | None,
) -> None:
    """採点可能・再実行要求・テストケース不在は既存の状態表示として扱う。"""
    stage_paths = [StagePath.list_paths([CASE])[0]] if has_testcase else []
    paths = Mock()
    paths.execute.return_value = stage_paths
    getter = Mock()
    getter.execute.return_value = _stage_result()
    rollback = Mock()
    rollback.execute.return_value = StageTest if rollback_needed else None
    student_service = Mock()
    student_service.execute.return_value = _student()
    mark_service = Mock()
    mark_service.execute.return_value = StudentMark(student_id=STUDENT, score=None)
    usecase = StudentMarkViewDataGetMarkSummaryUseCase(
        student_get_service=student_service,
        student_mark_get_sub_service=mark_service,
        stage_path_list_sub_service=paths,
        student_stage_path_result_get_service=getter,
        student_stage_path_result_check_rollback_service=rollback,
    )

    summary = usecase.execute(STUDENT)
    assert summary.state is expected_state
    assert summary.is_ready is (expected_state is StudentMarkState.READY)
    if expected_reason is None:
        with pytest.raises(ValueError, match="no reason found"):
            _ = summary.reason
    else:
        assert summary.reason == expected_reason


def _project_init_usecase():
    """実ファイルを開かず、各初期化工程の例外変換だけを検証する。"""
    dependency_names = (
        "manaba_report_archive_gateway",
        "readonly_excel_worksheet_gateway",
        "manaba_report_list_parser",
        "manaba_report_list_archive_validate_service",
        "student_master_create_service",
        "student_submission_extract_service",
        "current_project_set_initialized_service",
    )
    dependencies = {name: Mock() for name in dependency_names}
    dependencies["manaba_report_archive_gateway"].read_from_path.return_value.read_report_list_excel_bytes.return_value = b"excel"
    return CurrentProjectInitializeStaticUseCase(**dependencies), dependencies


@pytest.mark.parametrize(
    ("dependency_name", "method", "error_type"),
    [
        ("manaba_report_archive_gateway", "read_from_path", ManabaReportArchiveError),
        ("readonly_excel_worksheet_gateway", "read_from_bytes", ReadonlyExcelWorksheetGatewayError),
        ("manaba_report_list_parser", "parse_worksheet", ManabaReportListParserError),
        ("manaba_report_list_archive_validate_service", "execute", ManabaReportListArchiveValidateServiceError),
        ("student_master_create_service", "execute", StudentMasterServiceError),
        ("student_submission_extract_service", "execute", StudentSubmissionServiceError),
    ],
)
def test_project_initialization_returns_exact_error_message(
        dependency_name: str, method: str, error_type: type[Exception],
) -> None:
    """初期化工程の既知の例外は理由全文を変更せず結果へ変換する。"""
    usecase, deps = _project_init_usecase()
    message = "初期化中にエラーが発生しました。\n詳細: test.xlsx"
    getattr(deps[dependency_name], method).side_effect = error_type(reason=message)
    progress: list[str] = []

    result = usecase.execute(
        manaba_report_archive_fullpath=Path("test.zip"),
        progress_callback=progress.append,
    )
    assert result.has_error
    assert result.message == message
    assert "初期化を完了しています" not in progress
    deps["current_project_set_initialized_service"].execute.assert_not_called()


def test_unexpected_project_initialization_exception_propagates() -> None:
    """未知の例外は正常なエラー結果に変換せず、呼び出し元に伝播する。"""
    usecase, deps = _project_init_usecase()
    deps["manaba_report_list_parser"].parse_worksheet.side_effect = RuntimeError("unexpected")
    with pytest.raises(RuntimeError, match="unexpected"):
        usecase.execute(manaba_report_archive_fullpath=Path("test.zip"))
    deps["current_project_set_initialized_service"].execute.assert_not_called()


def test_project_initialization_success_message_and_progress() -> None:
    """正常終了時の進捗表示とエラーなしの結果を固定する。"""
    usecase, deps = _project_init_usecase()
    progress: list[str] = []
    result = usecase.execute(
        manaba_report_archive_fullpath=Path("test.zip"),
        progress_callback=progress.append,
    )
    assert not result.has_error
    assert result.message is None
    assert progress == [
        "提出アーカイブを読み込んでいます",
        "生徒マスタExcelを読み込んでいます",
        "生徒マスタを生成しています",
        "生徒の提出ファイルを展開しています",
        "初期化を完了しています",
    ]
    deps["current_project_set_initialized_service"].execute.assert_called_once_with()


@pytest.mark.parametrize(
    ("config_state", "message"),
    [
        (ProjectConfigState.INCOMPATIBLE_APP_VERSION, "現在のバージョンと互換性がありません"),
        (ProjectConfigState.UNOPENABLE, "プロジェクトデータが破損していて開けません"),
        (ProjectConfigState.META_BROKEN, "メタデータが破損していて読み取れません"),
    ],
)
def test_recent_project_error_summary_exact_message(
        config_state: ProjectConfigState, message: str,
) -> None:
    """最近のプロジェクト一覧では状態に応じた固定メッセージを表示する。"""
    project_id = ProjectID("sample_project")
    project_ids = Mock()
    project_ids.execute.return_value = [project_id]
    project_config = Mock()
    project_config.execute.return_value = config_state
    repository = Mock()
    usecase = ProjectListRecentSummaryUseCase(
        project_list_id_query_service=project_ids,
        project_get_config_state_query_service=project_config,
        project_repo=repository,
    )

    results = usecase.execute()
    assert len(results) == 1
    assert results[0].has_error
    assert results[0].project_id == project_id
    assert results[0].error_message == message
    repository.get.assert_not_called()


def test_recent_project_normal_summary_is_not_an_error() -> None:
    """正常なプロジェクトはエラー用メッセージを持たない。"""
    project_id = ProjectID("sample_project")
    project_ids = Mock()
    project_ids.execute.return_value = [project_id]
    project_config = Mock()
    project_config.execute.return_value = ProjectConfigState.NORMAL
    repository = Mock()
    repository.get.return_value = Mock(
        project_id=project_id,
        target_id=TargetID(2),
        zip_name="sample.zip",
        open_at=MTIME,
    )
    usecase = ProjectListRecentSummaryUseCase(
        project_list_id_query_service=project_ids,
        project_get_config_state_query_service=project_config,
        project_repo=repository,
    )

    results = usecase.execute()
    assert len(results) == 1
    assert not results[0].has_error
    assert results[0].target_number == 2
    assert results[0].zip_name == "sample.zip"
    with pytest.raises(ValueError, match="project has no error"):
        _ = results[0].error_message
