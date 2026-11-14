"""サービスと外部IOの例外変換および中断処理の既存契約を固定する。"""

import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest

from autoprogen.domain.error import (
    CompileToolIOError,
    StopTask,
    StorageRunCompilerServiceError,
)
from autoprogen.domain.error.stage.build import (
    SourceFilenameMultipleNumbersError,
    SourceFilenameNoNumberError,
)
from autoprogen.domain.error.stage.compile import (
    CompileSourceNotFoundError,
    CompilerDiagnosticError,
    CompilerExecutionFailedError,
    CompilerInputFileNotFoundError,
    CompilerNotConfiguredError,
    CompilerTimeoutError,
    CompilerWorkingDirectoryNotFoundError,
    VsDevToolNotFoundError,
)
from autoprogen.domain.error.stage.execute import (
    ExecutableNotFoundError,
    ExecutionTimeoutError,
)
from autoprogen.domain.model.stage_path import StagePath
from autoprogen.domain.model.value import StudentID, TestCaseID as CaseID, TargetID
from autoprogen.infra.io.compile_tool import CompileToolIO, _VSDevTool
from autoprogen.infra.io.executable import ExecutableIOTimeoutError
from autoprogen.service.storage_run_compiler import StorageRunCompilerService
from autoprogen.service.storage_run_executable import StorageRunExecutableService
from autoprogen.service.student_submission import (
    StudentSubmissionListSourceRelativePathQueryService,
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


@pytest.mark.parametrize("configured,source_exists,error_type", [
    (False, True, CompilerNotConfiguredError),
    (True, False, CompileSourceNotFoundError),
])
def test_compiler_preconditions_raise_specific_errors(
        configured: bool,
        source_exists: bool,
        error_type: type[CompilerNotConfiguredError | CompileSourceNotFoundError],
) -> None:
    """コンパイラ未設定・対象不在を具体的なCOMPILEエラーで区別する。"""
    service, tool, _ = _compiler_service(configured=configured, source_exists=source_exists)
    with pytest.raises(StorageRunCompilerServiceError) as raised:
        service.execute(storage_id="storage-id", source_file_relative_path=SOURCE_PATH)
    assert isinstance(raised.value.error, error_type)
    assert raised.value.output is None
    tool.run_and_get_output.assert_not_called()


@pytest.mark.parametrize("output", ["main.c(1): error C2143\n", None])
def test_compiler_io_failure_preserves_reason_and_raw_output(output: str | None) -> None:
    """IOの失敗をService例外へ変換しても、コンパイラ生出力を失わない。"""
    service, tool, _ = _compiler_service()
    tool.run_and_get_output.side_effect = CompileToolIOError(
        error=CompilerDiagnosticError(), output=output,
    )
    with pytest.raises(StorageRunCompilerServiceError) as raised:
        service.execute(storage_id="storage-id", source_file_relative_path=SOURCE_PATH)
    assert isinstance(raised.value.error, CompilerDiagnosticError)
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
    assert isinstance(raised.value.error, CompilerTimeoutError)
    assert raised.value.output is None


@pytest.mark.parametrize("case,error_type", [
    ("devtool", VsDevToolNotFoundError),
    ("working_directory", CompilerWorkingDirectoryNotFoundError),
    ("input_file", CompilerInputFileNotFoundError),
])
def test_compile_tool_paths_raise_specific_errors(
        tmp_path: Path,
        case: str,
        error_type: type[
            VsDevToolNotFoundError
            | CompilerWorkingDirectoryNotFoundError
            | CompilerInputFileNotFoundError
        ],
) -> None:
    """コンパイラ起動前のパス検証を具体的なCOMPILEエラーで区別する。"""
    devcmd = tmp_path / "VsDevCmd.bat"
    cwd = tmp_path
    target = Path("main.c")
    if case != "devtool":
        devcmd.write_text("@echo off\n", encoding="utf-8")
    if case == "working_directory":
        cwd = tmp_path / "missing"
    elif case == "input_file":
        target = Path("missing.c")

    with pytest.raises(CompileToolIOError) as raised:
        CompileToolIO.run_and_get_output(
            compiler_tool_fullpath=devcmd,
            timeout=3,
            cwd_fullpath=cwd,
            target_relative_path=target,
        )

    assert isinstance(raised.value.error, error_type)
    assert raised.value.error.path == (
        devcmd if case == "devtool" else cwd if case == "working_directory" else cwd / target
    )
    assert raised.value.output is None


@pytest.mark.parametrize("output,error_type", [
    ("Microsoft (R) C/C++ Compiler\nCopyright (C) Microsoft Corporation\n",
     CompilerDiagnosticError),
    ("'cl' is not recognized\n", CompilerExecutionFailedError),
])
def test_compile_tool_process_failure_raises_specific_error(
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        output: str,
        error_type: type[CompilerDiagnosticError | CompilerExecutionFailedError],
) -> None:
    """プロセス失敗をコンパイラ診断と起動失敗に分類する。"""
    devcmd = tmp_path / "VsDevCmd.bat"
    devcmd.write_text("@echo off\n", encoding="utf-8")
    source = tmp_path / "main.c"
    source.write_text("int main(void) {return 0;}\n", encoding="utf-8")

    def _fail(self):
        """実際のコンパイラを起動せず指定した出力で失敗させる。"""
        raise subprocess.CalledProcessError(1, "cl", output=output)

    monkeypatch.setattr(_VSDevTool, "_run_and_get_output", _fail)
    with pytest.raises(CompileToolIOError) as raised:
        CompileToolIO.run_and_get_output(
            compiler_tool_fullpath=devcmd,
            timeout=3,
            cwd_fullpath=tmp_path,
            target_relative_path=Path("main.c"),
        )

    assert isinstance(raised.value.error, error_type)
    assert raised.value.output == output


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
    """実行対象不在ではIOを呼ばず、具体的なEXECUTEエラーを返す。"""
    service, io = _executable_service(exists=False)
    with pytest.raises(ExecutableNotFoundError):
        service.execute(
            storage_id="storage-id", executable_file_relative_path=Path("main.exe"), timeout=1.0
        )
    io.run.assert_not_called()


def test_execute_io_timeout_reason_is_exact() -> None:
    """IOタイムアウトを具体的なEXECUTEエラーへ変換する。"""
    service, io = _executable_service(exists=True)
    io.run.side_effect = ExecutableIOTimeoutError()
    with pytest.raises(ExecutionTimeoutError):
        service.execute(
            storage_id="storage-id", executable_file_relative_path=Path("main.exe"), timeout=1.0
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


@pytest.mark.parametrize("filename,error_type", [
    ("prog.c", SourceFilenameNoNumberError),
    ("prog2_3.c", SourceFilenameMultipleNumbersError),
])
def test_source_filename_validation_raises_specific_error(
        filename: str,
        error_type: type[SourceFilenameNoNumberError | SourceFilenameMultipleNumbersError],
) -> None:
    """ファイル名不正は原因を表す具体的なBUILDエラーとして通知する。"""
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
    with pytest.raises(error_type) as raised:
        service.execute(student_id=STUDENT)
    assert raised.value.file_relative_path == Path(filename)
    if isinstance(raised.value, SourceFilenameMultipleNumbersError):
        assert raised.value.numbers == ("2", "3")


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
