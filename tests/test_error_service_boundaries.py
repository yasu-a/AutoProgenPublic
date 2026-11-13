"""サービスと外部IOの例外変換および中断処理の既存契約を固定する。"""

import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest

from autoprogen.domain.error import (
    CompileToolIOError,
    StopTask,
    StorageRunCompilerServiceError,
    StorageRunExecutableServiceError,
)
from autoprogen.domain.model.stage_path import StagePath
from autoprogen.domain.model.value import StudentID, TestCaseID as CaseID, TargetID
from autoprogen.infra.io.compile_tool import CompileToolIO, _VSDevTool
from autoprogen.infra.io.executable import ExecutableIOTimeoutError
from autoprogen.service.storage_run_compiler import StorageRunCompilerService
from autoprogen.service.storage_run_executable import StorageRunExecutableService
from autoprogen.service.student_submission import (
    StudentSubmissionListSourceRelativePathQueryService,
    StudentSubmissionListSourceRelativePathQueryServiceError,
)
from autoprogen.usecase.student_run_next_stage import StudentRunNextStageUseCase


STUDENT = StudentID("00A0000000A")
SOURCE_PATH = Path("main.c")


def _compiler_service(*, configured: bool = True, source_exists: bool = True):
    """MSVCを起動せずにコンパイラServiceの設定・ストレージを用意する。"""
    settings_repo = Mock()
    settings_repo.get.return_value.compiler_tool_fullpath = (
        Path("/fake/VsDevCmd.bat") if configured else None
    )
    settings_repo.get.return_value.compile_timeout = 3.5
    storage_repo = Mock()
    storage_repo.get.return_value.files = [SOURCE_PATH] if source_exists else []
    storage_repo.get.return_value.base_folder_fullpath = Path("/fake/storage")
    compiler_tool = Mock()
    service = StorageRunCompilerService(
        compile_tool_io=compiler_tool,
        global_settings_repo=settings_repo,
        storage_repo=storage_repo,
    )
    return service, compiler_tool, storage_repo


@pytest.mark.parametrize("configured,source_exists,expected", [
    (False, True, "コンパイラが設定されていません"),
    (True, False, "コンパイル対象が存在しません"),
])
def test_compiler_preconditions_preserve_reasons(
        configured: bool, source_exists: bool, expected: str,
) -> None:
    """コンパイラ未設定・対象不在では正確な理由を持つ例外を返す。"""
    service, tool, _ = _compiler_service(configured=configured, source_exists=source_exists)
    with pytest.raises(StorageRunCompilerServiceError) as raised:
        service.execute(storage_id="storage-id", source_file_relative_path=SOURCE_PATH)
    assert raised.value.reason == expected
    assert raised.value.output is None
    tool.run_and_get_output.assert_not_called()


@pytest.mark.parametrize("output", ["main.c(1): error C2143\n", None])
def test_compiler_io_failure_preserves_reason_and_raw_output(output: str | None) -> None:
    """IOの失敗をService例外へ変換しても、コンパイラ生出力を失わない。"""
    service, tool, _ = _compiler_service()
    tool.run_and_get_output.side_effect = CompileToolIOError(
        reason="コンパイルエラーが発生しました", output=output,
    )
    with pytest.raises(StorageRunCompilerServiceError) as raised:
        service.execute(storage_id="storage-id", source_file_relative_path=SOURCE_PATH)
    assert raised.value.reason == (
        "コンパイルに失敗しました。ソースコードを直接Visual Studioで開いて実行してください．\n"
        "文字コードが原因の場合、Visual Studioで実行すると正常に動作することがあります。\n"
        "コンパイルエラーが発生しました"
    )
    assert raised.value.output == output


def test_unexpected_compiler_io_error_propagates() -> None:
    """IOの想定外エラーはコンパイル失敗へ無条件に変換しない。"""
    service, tool, _ = _compiler_service()
    tool.run_and_get_output.side_effect = OSError("compiler process unavailable")
    with pytest.raises(OSError, match="compiler process unavailable"):
        service.execute(storage_id="storage-id", source_file_relative_path=SOURCE_PATH)


def test_compile_tool_io_timeout_conversion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """コンパイラIOはタイムアウトをCompileToolIOErrorへ変換する。"""
    devcmd = tmp_path / "VsDevCmd.bat"
    devcmd.write_text("@echo off\n", encoding="utf-8")
    source = tmp_path / "main.c"
    source.write_text("int main(void) {return 0;}\n", encoding="utf-8")

    def _timeout(self):
        """実際のコマンドは起動せずタイムアウトだけを再現する。"""
        raise subprocess.TimeoutExpired(cmd="cl", timeout=3)

    monkeypatch.setattr(_VSDevTool, "_run_and_get_output", _timeout)
    with pytest.raises(CompileToolIOError) as raised:
        CompileToolIO.run_and_get_output(
            compiler_tool_fullpath=devcmd,
            timeout=3,
            cwd_fullpath=tmp_path,
            target_relative_path=Path("main.c"),
        )
    assert raised.value.reason == "コンパイラからの応答がタイムアウトしました"
    assert raised.value.output is None


def _executable_service(*, exists: bool):
    """プログラムは起動せず、実行Serviceの例外処理を確認する。"""
    storage_repo = Mock()
    storage_repo.get.return_value.files = [Path("main.exe")] if exists else []
    storage_repo.get.return_value.base_folder_fullpath = Path("/fake/storage")
    executable_io = Mock()
    service = StorageRunExecutableService(
        storage_repo=storage_repo, executable_io=executable_io,
    )
    return service, executable_io


def test_execute_missing_executable_reason() -> None:
    """実行対象不在ではIOを呼ばず、従来のService例外を返す。"""
    service, io = _executable_service(exists=False)
    with pytest.raises(StorageRunExecutableServiceError) as raised:
        service.execute(
            storage_id="storage-id", executable_file_relative_path=Path("main.exe"), timeout=1.0
        )
    assert raised.value.reason == "実行対象が存在しません"
    io.run.assert_not_called()


def test_execute_io_timeout_reason_is_exact() -> None:
    """IOタイムアウトは規定の改行を含む実行Service例外へ変換する。"""
    service, io = _executable_service(exists=True)
    io.run.side_effect = ExecutableIOTimeoutError()
    with pytest.raises(StorageRunExecutableServiceError) as raised:
        service.execute(
            storage_id="storage-id", executable_file_relative_path=Path("main.exe"), timeout=1.0
        )
    assert raised.value.reason == (
        "実行がタイムアウトしました\n"
        "この環境のスペックに対して並列タスク数が多すぎる・"
        "プログラムが入力を待っている・無限ループしているなどの可能性があります"
    )
    io.run.assert_called_once()


def test_execute_unexpected_io_error_propagates() -> None:
    """想定外の実行IOエラーは既存どおり伝播する。"""
    service, io = _executable_service(exists=True)
    io.run.side_effect = RuntimeError("unexpected executable fault")
    with pytest.raises(RuntimeError, match="unexpected executable fault"):
        service.execute(
            storage_id="storage-id", executable_file_relative_path=Path("main.exe"), timeout=1.0
        )


@pytest.mark.parametrize("filename,expected_detail", [
    ("prog.c", "ファイル名に数字が含まれていません。"),
    ("prog2_3.c", "ファイル名に数字が複数含まれています: 2, 3"),
])
def test_source_filename_validation_preserves_error_details(
        filename: str, expected_detail: str,
) -> None:
    """ファイル名不正は分類された例外と元の詳細メッセージを返す。"""
    layout = Mock()
    layout.student_submission_dir.return_value = Path("/fake/reports")
    core_io = Mock()
    core_io.walk_files.return_value = [Path(filename)]
    project_repo = Mock()
    project_repo.get.return_value.target_id = TargetID(2)
    service = StudentSubmissionListSourceRelativePathQueryService(
        project_path_layout=layout,
        current_project_core_io=core_io,
        current_project_repo=project_repo,
    )
    with pytest.raises(StudentSubmissionListSourceRelativePathQueryServiceError) as raised:
        service.execute(student_id=STUDENT)
    assert raised.value.reason == (
        f"ファイル名{filename}から設問番号を判別できません。\n"
        + expected_detail
    )


def test_stop_task_propagates_without_writing_student_failure() -> None:
    """停止要求はステージ失敗ではなくStopTaskとして上位へ伝わる。"""
    stage_list = Mock()
    stage_list.execute.return_value = StagePath.list_paths([CaseID("case01")])
    stage_put = Mock()
    build = Mock()
    compile_stage = Mock()
    execute_stage = Mock()
    test_stage = Mock()
    usecase = StudentRunNextStageUseCase(
        stage_path_list_sub_service=stage_list,
        student_stage_path_result_get_service=Mock(),
        student_stage_path_result_repo=Mock(),
        student_stage_path_result_put_service=stage_put,
        student_run_build_stage_usecase=build,
        student_run_compile_stage_usecase=compile_stage,
        student_run_execute_stage_usecase=execute_stage,
        student_run_test_stage_usecase=test_stage,
        student_stage_path_result_check_rollback_service=Mock(),
    )
    with pytest.raises(StopTask):
        usecase.execute(student_id=STUDENT, stop_producer=lambda: True)
    stage_put.execute.assert_not_called()
    build.execute.assert_not_called()
    compile_stage.execute.assert_not_called()
    execute_stage.execute.assert_not_called()
    test_stage.execute.assert_not_called()
