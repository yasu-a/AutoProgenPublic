"""BUILD〜TESTの失敗結果と例外境界の既存動作を固定する。"""

import hashlib
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest

from autoprogen.domain.error import (
    MatchServiceError,
    StorageRunCompilerServiceError,
    StorageRunExecutableServiceError,
)
from autoprogen.domain.model.output_file import OutputFile, OutputFileCollection
from autoprogen.domain.model.project_settings import ProjectSettings
from autoprogen.domain.model.stage_path import StagePath
from autoprogen.domain.model.student_stage_result import (
    BuildFailureStudentStageResult,
    BuildSuccessStudentStageResult,
    CompileFailureStudentStageResult,
    ExecuteFailureStudentStageResult,
    ExecuteSuccessStudentStageResult,
    TestFailureStudentStageResult as StudentTestFailureStageResult,
    TestSuccessStudentStageResult as StudentTestSuccessStageResult,
)
from autoprogen.domain.model.value import FileID, StudentID, TestCaseID as CaseID
from autoprogen.domain.service.source_code_check import SourceCodeCheckService
from autoprogen.domain.service.source_code_check_factory import SourceCodeCheckCatalogFactory
from autoprogen.service.student_submission import (
    StudentSubmissionGetSourceContentService,
    StudentSubmissionListSourceRelativePathQueryServiceError,
)
from autoprogen.usecase.student_run_build import StudentRunBuildStageUseCase
from autoprogen.usecase.student_run_compile import StudentRunCompileStageUseCase
from autoprogen.usecase.student_run_execute import StudentRunExecuteStageUseCase
from autoprogen.usecase.student_run_test import StudentRunTestStageUseCase


STUDENT = StudentID("00A0000000A")
TESTCASE = CaseID("case01")
STAGE_PATH = StagePath.list_paths([TESTCASE])[0]
SAFE_SOURCE = b"int main(void) { return 0; }\n"
BLOCKED_SOURCE = b'int main(void) { system("echo test"); return 0; }\n'


def _saved_result(put_service: Mock):
    """Mockに記録されたステージ結果を取り出す。"""
    put_service.execute.assert_called_once()
    assert put_service.execute.call_args.kwargs["stage_path"] == STAGE_PATH
    return put_service.execute.call_args.kwargs["result"]


def _build_case(case: str):
    """実際のソース抽出ServiceとBUILD UseCaseをMock依存先で構成する。"""
    student_repo = Mock()
    student_repo.get.return_value.is_submitted = case != "not_submitted"
    source_list = Mock()
    source_list.execute.return_value = [Path("prog02.c")]
    file_content = Mock()
    file_content.execute.return_value = b"int main(void) {return 0;}\n"

    if case == "no_source":
        source_list.execute.return_value = []
    elif case == "multiple_sources":
        source_list.execute.return_value = [Path("prog02.c"), Path("prog2.c")]
    elif case == "invalid_filename":
        source_list.execute.side_effect = StudentSubmissionListSourceRelativePathQueryServiceError(
            "ファイル名prog2_3.cから設問番号を判別できません。\n"
            "ファイル名に数字が複数含まれています: 2, 3"
        )
    elif case == "invalid_encoding":
        file_content.execute.side_effect = UnicodeError("decode failed")

    source_service = StudentSubmissionGetSourceContentService(
        student_submission_list_source_relative_path_query_service=source_list,
        student_submission_get_file_content_query_service=file_content,
        student_repo=student_repo,
    )
    clear = Mock()
    set_source = Mock()
    checksum = Mock()
    checksum.execute.return_value = 103
    put = Mock()
    usecase = StudentRunBuildStageUseCase(
        student_submission_get_source_content_service=source_service,
        student_dynamic_clear_service=clear,
        student_dynamic_set_source_content_service=set_source,
        student_submission_get_checksum_service=checksum,
        student_put_stage_result_service=put,
    )
    return usecase, source_list, clear, set_source, checksum, put


@pytest.mark.parametrize("case,expected", [
    ("not_submitted", "未提出の学生です。"),
    ("no_source", "提出物にソースファイルが見つかりませんでした。"),
    ("multiple_sources", "提出物に複数のソースファイルが見つかりました。\nprog02.c\nprog2.c"),
    ("invalid_filename", "提出フォルダからソースファイルを抽出中にエラーが発生しました。\n"
                         "ファイル名prog2_3.cから設問番号を判別できません。\n"
                         "ファイル名に数字が複数含まれています: 2, 3"),
    ("invalid_encoding", "ソースファイルの文字コードが判定できません。\nファイル名: prog02.c\n"),
])
def test_build_failure_contract(case: str, expected: str) -> None:
    """ソース抽出の代表的な失敗は、従来の全文をBUILD失敗に保存する。"""
    usecase, _, clear, set_source, checksum, put = _build_case(case)
    usecase.execute(STUDENT, STAGE_PATH)
    result = _saved_result(put)
    assert type(result) is BuildFailureStudentStageResult
    assert not result.is_success
    assert result.student_id == STUDENT
    assert result.reason == expected
    assert result.detailed_text == expected
    clear.execute.assert_called_once_with(student_id=STUDENT)
    set_source.execute.assert_not_called()
    checksum.execute.assert_not_called()


def test_build_success_contrast() -> None:
    """BUILD成功時はソースを配置し、チェックサム付き成功結果を保存する。"""
    usecase, _, clear, set_source, checksum, put = _build_case("success")
    usecase.execute(STUDENT, STAGE_PATH)
    result = _saved_result(put)
    assert type(result) is BuildSuccessStudentStageResult
    assert result.is_success
    assert result.submission_folder_checksum == 103
    clear.execute.assert_called_once()
    set_source.execute.assert_called_once_with(
        student_id=STUDENT, source_content_text="int main(void) {return 0;}\n"
    )
    checksum.execute.assert_called_once_with(student_id=STUDENT)


def test_build_unexpected_exception_propagates() -> None:
    """想定外の例外は学生のBUILD失敗に変換されない。"""
    usecase, source_list, clear, _, _, put = _build_case("success")
    source_list.execute.side_effect = RuntimeError("unexpected extraction error")
    with pytest.raises(RuntimeError, match="unexpected extraction error"):
        usecase.execute(STUDENT, STAGE_PATH)
    clear.execute.assert_called_once()
    put.execute.assert_not_called()


def _compile_case(source: bytes):
    """ソース安全性チェックは実物、MSVCはMockにしたCOMPILE UseCaseを返す。"""
    storage_create = Mock()
    storage_create.execute.return_value = "storage-1"
    storage_load = Mock()
    storage_load.execute.return_value = source
    storage_store = Mock()
    compiler = Mock()
    storage_delete = Mock()
    put = Mock()
    settings = Mock()
    settings.get.return_value = ProjectSettings.create_default()
    usecase = StudentRunCompileStageUseCase(
        storage_create_service=storage_create,
        storage_load_student_source_service=storage_load,
        storage_store_student_executable_service=storage_store,
        source_code_check_catalog_factory=SourceCodeCheckCatalogFactory(),
        source_code_check_service=SourceCodeCheckService(),
        project_settings_repository=settings,
        storage_run_compiler_service=compiler,
        storage_delete_service=storage_delete,
        student_put_stage_result_service=put,
    )
    return usecase, compiler, storage_store, storage_delete, put


def test_compile_safety_check_failure_message_and_short_circuit() -> None:
    """検出行・SHA-256を含む全文を固定し、コンパイラが動かないことを確認する。"""
    usecase, compiler, store, delete, put = _compile_case(BLOCKED_SOURCE)
    usecase.execute(STUDENT, STAGE_PATH)
    result = _saved_result(put)
    assert type(result) is CompileFailureStudentStageResult
    assert not result.is_success
    assert result.output == ""
    assert result.reason == (
        "ソースコードの安全性チェックで問題が検出されたため、コンパイルを停止しました。\n"
        f"検査対象SHA-256: {hashlib.sha256(BLOCKED_SOURCE).hexdigest()}\n"
        "1行目: [process.system] 外部コマンドの実行"
    )
    assert result.detailed_text == result.reason + "\n"
    compiler.execute.assert_not_called()
    store.execute.assert_not_called()
    delete.execute.assert_called_once_with("storage-1")


def test_compile_decode_failure_message_and_cleanup() -> None:
    """検査不能な文字コードの文言と一時ストレージ削除を固定する。"""
    usecase, compiler, store, delete, put = _compile_case(b"\x80\x81")
    usecase.execute(STUDENT, STAGE_PATH)
    result = _saved_result(put)
    assert type(result) is CompileFailureStudentStageResult
    assert result.reason == (
        "ソースコードの安全性チェックに失敗しました。\n"
        "ソースコードをUTF-8として読み込めませんでした。"
    )
    assert result.output == ""
    compiler.execute.assert_not_called()
    store.execute.assert_not_called()
    delete.execute.assert_called_once_with("storage-1")


@pytest.mark.parametrize("compiler_output", ["fatal error C1004\n", None])
def test_compile_service_exception_becomes_failure(compiler_output: str | None) -> None:
    """コンパイラServiceの失敗理由と生出力をそのまま記録する。"""
    usecase, compiler, store, delete, put = _compile_case(SAFE_SOURCE)
    compiler.execute.side_effect = StorageRunCompilerServiceError(
        reason="コンパイラからの応答がタイムアウトしました", output=compiler_output,
    )
    usecase.execute(STUDENT, STAGE_PATH)
    result = _saved_result(put)
    assert type(result) is CompileFailureStudentStageResult
    assert result.reason == "コンパイルに失敗しました。\nコンパイラからの応答がタイムアウトしました"
    assert result.output == (compiler_output or "")
    assert result.detailed_text == result.reason + "\n" + result.output
    store.execute.assert_not_called()
    delete.execute.assert_called_once_with("storage-1")


def test_compile_unexpected_exception_propagates_and_cleans_storage() -> None:
    """予期しない例外は失敗結果に変換せず、finallyで一時領域を削除する。"""
    usecase, compiler, _, delete, put = _compile_case(SAFE_SOURCE)
    compiler.execute.side_effect = RuntimeError("unexpected compiler fault")
    with pytest.raises(RuntimeError, match="unexpected compiler fault"):
        usecase.execute(STUDENT, STAGE_PATH)
    put.execute.assert_not_called()
    delete.execute.assert_called_once_with("storage-1")


def _execute_case(error: Exception):
    """実行対象と設定が存在するEXECUTE UseCaseを構成する。"""
    storage_create = Mock()
    storage_create.execute.return_value = "storage-1"
    storage_load = Mock()
    storage_input = Mock()
    snapshot = Mock()
    delete = Mock()
    put = Mock()
    settings = Mock()
    settings.get.return_value.execute_config.options.timeout = 1.5
    runner = Mock()
    runner.execute.side_effect = error
    write_stdout = Mock()
    usecase = StudentRunExecuteStageUseCase(
        storage_create_service=storage_create,
        storage_load_student_executable_service=storage_load,
        storage_load_execute_config_input_files_service=storage_input,
        storage_take_snapshot_service=snapshot,
        storage_delete_service=delete,
        student_put_stage_result_service=put,
        testcase_config_get_execute_config_mtime_service=Mock(),
        storage_run_executable_service=runner,
        testcase_config_repo=settings,
        storage_create_output_file_mapping_from_diff_service=Mock(),
        storage_write_stdout_file_service=write_stdout,
    )
    return usecase, runner, write_stdout, delete, put


def test_execute_expected_exception_becomes_failure() -> None:
    """プログラム実行のタイムアウトはEXECUTE失敗に変換される。"""
    message = "実行がタイムアウトしました\n理由は入力待ちかもしれません"
    usecase, runner, stdout, delete, put = _execute_case(
        StorageRunExecutableServiceError(reason=message)
    )
    usecase.execute(STUDENT, STAGE_PATH)
    result = _saved_result(put)
    assert type(result) is ExecuteFailureStudentStageResult
    assert not result.is_success
    assert result.testcase_id == TESTCASE
    assert result.reason == message
    assert result.detailed_text == message
    runner.execute.assert_called_once_with(
        storage_id="storage-1", executable_file_relative_path=Path("main.exe"), timeout=1.5
    )
    stdout.execute.assert_not_called()
    # 現行実装ではこの経路もfinallyで一時ストレージを削除する。
    delete.execute.assert_called_once_with(storage_id="storage-1")


def test_execute_unexpected_exception_is_not_saved() -> None:
    """想定外の実行エラーはステージ失敗に変換されない。"""
    usecase, _, _, delete, put = _execute_case(RuntimeError("runner crashed"))
    with pytest.raises(RuntimeError, match="runner crashed"):
        usecase.execute(STUDENT, STAGE_PATH)
    put.execute.assert_not_called()
    # 現行実装では想定外の例外でもfinallyで一時ストレージを削除する。
    delete.execute.assert_called_once_with(storage_id="storage-1")


def _test_case(execute_result):
    """EXECUTE結果の有無を切り替えられるTEST UseCaseを構成する。"""
    get_stage = Mock()
    get_stage.execute.return_value = execute_result
    put = Mock()
    settings = Mock()
    settings.get.return_value.test_config.expected_output_file_collection.file_ids = []
    test_config_mtime = Mock()
    test_config_mtime.execute.return_value = datetime(2026, 1, 1)
    usecase = StudentRunTestStageUseCase(
        testcase_config_repo=settings,
        student_put_stage_result_service=put,
        student_get_stage_result_service=get_stage,
        testcase_config_get_test_config_mtime_service=test_config_mtime,
        match_get_best_service=Mock(),
    )
    return usecase, settings, put


@pytest.mark.parametrize("found,expected", [
    (False, "実行結果が見つかりません"),
    (True, "失敗した実行のテストはできません"),
])
def test_test_stage_cannot_test_unavailable_execution(found: bool, expected: str) -> None:
    """EXECUTE結果なし・失敗の両方がTEST失敗に変換される。"""
    prior = None if not found else ExecuteFailureStudentStageResult.create_instance(
        student_id=STUDENT, testcase_id=TESTCASE, reason="実行がタイムアウトしました"
    )
    usecase, _, put = _test_case(prior)
    usecase.execute(STUDENT, STAGE_PATH)
    result = _saved_result(put)
    assert type(result) is StudentTestFailureStageResult
    assert not result.is_success
    assert result.reason == expected
    assert result.testcase_id == TESTCASE


def test_test_stage_match_error_is_converted_to_failure() -> None:
    """マッチングServiceの例外はTEST失敗に変換し、理由を引き継ぐ。"""
    file_id = FileID(Path("out.txt"))
    executed = ExecuteSuccessStudentStageResult.create_instance(
        student_id=STUDENT,
        testcase_id=TESTCASE,
        execute_config_mtime=datetime(2026, 1, 1),
        output_file_collection=OutputFileCollection([
            OutputFile(file_id=file_id, content="actual"),
        ]),
    )
    usecase, settings, put = _test_case(executed)
    expected_files = settings.get.return_value.test_config.expected_output_file_collection
    expected_files.file_ids = [file_id]
    expected_files.has.return_value = True
    expected_files.find.return_value.patterns = Mock()
    matcher = usecase._match_get_best_service
    matcher.execute.side_effect = MatchServiceError("マッチング失敗の理由")
    usecase.execute(STUDENT, STAGE_PATH)
    result = _saved_result(put)
    assert type(result) is StudentTestFailureStageResult
    assert result.reason == "マッチング失敗の理由"
    matcher.execute.assert_called_once()


def test_test_stage_wrong_answer_remains_success() -> None:
    """出力不足による不正解は例外でもTESTステージ失敗でもない。"""
    executed = ExecuteSuccessStudentStageResult.create_instance(
        student_id=STUDENT,
        testcase_id=TESTCASE,
        execute_config_mtime=datetime(2026, 1, 1),
        output_file_collection=OutputFileCollection(),
    )
    usecase, settings, put = _test_case(executed)
    file_id = FileID(Path("expected.txt"))
    expected_files = settings.get.return_value.test_config.expected_output_file_collection
    expected_files.file_ids = [file_id]
    expected_files.has.return_value = True
    expected_files.find.return_value.file_id = file_id
    usecase.execute(STUDENT, STAGE_PATH)
    result = _saved_result(put)
    assert type(result) is StudentTestSuccessStageResult
    assert result.is_success
    assert not result.is_accepted
    assert result.testcase_id == TESTCASE


def test_test_stage_unexpected_exception_propagates() -> None:
    """予期しない例外はTEST失敗として記録しない。"""
    usecase, _, put = _test_case(None)
    usecase._student_get_stage_result_service.execute.side_effect = RuntimeError("DB unavailable")
    with pytest.raises(RuntimeError, match="DB unavailable"):
        usecase.execute(STUDENT, STAGE_PATH)
    put.execute.assert_not_called()
