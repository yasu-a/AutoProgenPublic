import hashlib
from pathlib import Path
from unittest.mock import Mock

from autoprogen.domain.model.project_settings import (
    ProjectSettings,
    SourceCodeCheckIdentifier,
    SourceCodeCheckSkip,
)
from autoprogen.domain.model.student_stage_result import (
    CompileFailureStudentStageResult,
    CompileSuccessStudentStageResult,
)
from autoprogen.domain.model.value import StudentID
from autoprogen.service.dto.storage_run_compiler import StorageCompileServiceResult
from autoprogen.service.source_code_check import SourceCodeCheckService
from autoprogen.service.source_code_check_factory import SourceCodeCheckCatalogFactory
from autoprogen.usecase.student_run_compile import StudentRunCompileStageUseCase


STUDENT_ID = StudentID("00A0000000A")


def _create_usecase(source: bytes, settings: ProjectSettings):
    """コンパイラを起動しないCOMPILEステージのテスト環境を作る。"""
    storage_create = Mock()
    storage_create.execute.return_value = "storage-test"
    storage_load = Mock()
    storage_load.execute.return_value = source
    storage_store = Mock()
    compiler = Mock()
    compiler.execute.return_value = StorageCompileServiceResult(output="compiled")
    storage_delete = Mock()
    result_put = Mock()
    settings_repo = Mock()
    settings_repo.get.return_value = settings
    checker = SourceCodeCheckService()

    usecase = StudentRunCompileStageUseCase(
        storage_create_service=storage_create,
        storage_load_student_source_service=storage_load,
        storage_store_student_executable_service=storage_store,
        source_code_check_catalog_factory=SourceCodeCheckCatalogFactory(),
        source_code_check_service=checker,
        project_settings_repository=settings_repo,
        storage_run_compiler_service=compiler,
        storage_delete_service=storage_delete,
        student_put_stage_result_service=result_put,
    )
    return usecase, compiler, storage_store, storage_delete, result_put


def _execute(source: bytes, settings: ProjectSettings):
    """結果保存をMockに記録してCOMPILEを一度実行する。"""
    usecase, compiler, storage_store, storage_delete, result_put = _create_usecase(
        source, settings,
    )
    usecase.execute(STUDENT_ID, Mock())
    storage_delete.execute.assert_called_once_with("storage-test")
    result_put.execute.assert_called_once()
    return compiler, storage_store, result_put.execute.call_args.kwargs["result"]


def test_detected_rule_stops_before_compiler() -> None:
    """有効な規則を検出したらMSVCを呼ばず、失敗結果を保存する。"""
    compiler, storage_store, result = _execute(
        b'int main(void) { system("echo test"); return 0; }\n',
        ProjectSettings.create_default(),
    )
    compiler.execute.assert_not_called()
    storage_store.execute.assert_not_called()
    assert isinstance(result, CompileFailureStudentStageResult)
    assert "安全性チェック" in result.reason
    assert "process.system" in result.reason
    assert "1行目" in result.reason


def test_suppressed_rule_does_not_stop_compile() -> None:
    """プロジェクトで抑制した規則に一致してもコンパイルする。"""
    settings = ProjectSettings(
        suppressed_source_code_checks=frozenset({
            SourceCodeCheckIdentifier(group_id="process", check_id="system"),
        }),
        source_code_check_skips=frozenset(),
    )
    compiler, storage_store, result = _execute(
        b'int main(void) { system("echo test"); return 0; }\n',
        settings,
    )
    compiler.execute.assert_called_once()
    storage_store.execute.assert_called_once()
    assert isinstance(result, CompileSuccessStudentStageResult)


def test_approved_student_and_hash_bypass_check() -> None:
    """同一学生・同一ソースの許可履歴だけが検査を省略する。"""
    source = b'int main(void) { system("echo test"); return 0; }\n'
    settings = ProjectSettings(
        suppressed_source_code_checks=frozenset(),
        source_code_check_skips=frozenset({
            SourceCodeCheckSkip(
                student_id=STUDENT_ID,
                source_sha256=hashlib.sha256(source).hexdigest(),
            ),
        }),
    )
    compiler, _, result = _execute(source, settings)
    compiler.execute.assert_called_once()
    assert isinstance(result, CompileSuccessStudentStageResult)


def test_different_hash_is_not_approved() -> None:
    """ソースのバイト列が異なる場合は検査を行う。"""
    source = b'int main(void) { system("echo test"); return 0; }\n'
    settings = ProjectSettings(
        suppressed_source_code_checks=frozenset(),
        source_code_check_skips=frozenset({
            SourceCodeCheckSkip(student_id=STUDENT_ID, source_sha256="a" * 64),
        }),
    )
    compiler, _, result = _execute(source, settings)
    compiler.execute.assert_not_called()
    assert isinstance(result, CompileFailureStudentStageResult)


def test_different_student_is_not_approved() -> None:
    """別学生が許可されたハッシュだけでは検査を省略できない。"""
    source = b'int main(void) { system("echo test"); return 0; }\n'
    settings = ProjectSettings(
        suppressed_source_code_checks=frozenset(),
        source_code_check_skips=frozenset({
            SourceCodeCheckSkip(
                student_id=StudentID("00B0000000B"),
                source_sha256=hashlib.sha256(source).hexdigest(),
            ),
        }),
    )
    compiler, _, result = _execute(source, settings)
    compiler.execute.assert_not_called()
    assert isinstance(result, CompileFailureStudentStageResult)


def test_invalid_utf8_stops_before_compiler() -> None:
    """UTF-8として解釈できないソースも正常にCOMPILE失敗へ変換する。"""
    compiler, storage_store, result = _execute(
        b"\x80\x81\x82", ProjectSettings.create_default(),
    )
    compiler.execute.assert_not_called()
    storage_store.execute.assert_not_called()
    assert isinstance(result, CompileFailureStudentStageResult)
    assert "UTF-8" in result.reason


def test_safe_code_is_compiled() -> None:
    """検出なしなら既存のコンパイル処理を継続する。"""
    compiler, storage_store, result = _execute(
        b"int main(void) { return 0; }\n", ProjectSettings.create_default(),
    )
    compiler.execute.assert_called_once_with(
        storage_id="storage-test", source_file_relative_path=Path("main.c"),
    )
    storage_store.execute.assert_called_once()
    assert isinstance(result, CompileSuccessStudentStageResult)
