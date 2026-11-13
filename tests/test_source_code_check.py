import hashlib
import logging
from pathlib import Path
from unittest.mock import Mock

import pytest

from autoprogen.domain.model.file_item import SourceFileItem
from autoprogen.domain.model.source_code_check import SourceCodeCheckMatchType
from autoprogen.domain.model.value import StudentID
from autoprogen.service.storage import StorageLoadStudentSourceService
from autoprogen.service.source_code_check import (
    SourceCodeCheckCatalogFactory,
    SourceCodeCheckDecodeError,
    SourceCodeCheckService,
)
from autoprogen.service.dto.storage_run_compiler import StorageCompileServiceResult
from autoprogen.usecase.student_run_compile import StudentRunCompileStageUseCase


def test_source_code_check_catalog_has_unique_ids() -> None:
    """固定カタログの各階層で識別子が重複していないことを確認する。"""
    catalog = SourceCodeCheckCatalogFactory().create()

    group_ids = [group.group_id for group in catalog.groups]

    assert len(group_ids) == len(set(group_ids))
    for group in catalog.groups:
        check_ids = [entry.check_id for entry in group.entries]
        assert len(check_ids) == len(set(check_ids))
        assert all("." not in check_id for check_id in check_ids)
    assert catalog.entry_count == sum(len(group.entries) for group in catalog.groups)


def test_file_checks_include_standard_stream_io() -> None:
    """ファイル操作に基本的な標準ストリームI/Oが含まれることを確認する。"""
    catalog = SourceCodeCheckCatalogFactory().create()
    file_group = next(group for group in catalog.groups if group.group_id == "file")
    entries = {
        entry.check_id: entry
        for entry in file_group.entries
    }

    assert {"fscanf", "fgetc", "fgets"} <= set(
        entries["read"].target_strings,
    )
    assert {"fprintf", "fputc", "fputs"} <= set(
        entries["write"].target_strings,
    )
    assert {"fseek", "ftell", "rewind"} <= set(
        entries["position"].target_strings,
    )
    assert {"fflush", "setvbuf", "fclose", "tmpfile"} <= {
        target
        for check_id in (
            "stream_control",
            "close",
            "temporary",
        )
        for target in entries[check_id].target_strings
    }


def test_source_code_check_service_logs_start(
        caplog: pytest.LogCaptureFixture,
) -> None:
    """空実装の検査サービスがコンパイル対象を受け取って開始ログを残すことを確認する。"""
    service = SourceCodeCheckService(
        catalog_factory=SourceCodeCheckCatalogFactory(),
    )

    with caplog.at_level(logging.INFO):
        service.execute(source_code_bytes=b"int main(void) { return 0; }")

    assert "SOURCE CODE SAFETY CHECK STARTED" in caplog.text


def test_source_code_check_detects_function_calls_and_hash() -> None:
    """危険な関数呼び出しを行番号付きで検出し、入力バイト列をハッシュ化する。"""
    source_code_bytes = (
        b"#include <stdlib.h>\n"
        b"int main(void) {\n"
        b"    system(\"echo test\");\n"
        b"}\n"
    )
    service = SourceCodeCheckService(
        catalog_factory=SourceCodeCheckCatalogFactory(),
    )

    result = service.execute(source_code_bytes=source_code_bytes)

    system_findings = [
        finding
        for finding in result.findings
        if finding.group_id == "process" and finding.check_id == "system"
    ]
    assert len(system_findings) == 1
    assert system_findings[0].line_number == 3
    assert result.source_sha256 == hashlib.sha256(source_code_bytes).hexdigest()


def test_source_code_check_ignores_function_names_in_comments_and_strings() -> None:
    """コメントと文字列内にある関数名を関数呼び出しとして検出しない。"""
    source_code_bytes = (
        b"// system(\"comment\");\n"
        b"const char *message = \"system(ignored)\";\n"
        b"/* CreateProcessW(ignored); */\n"
        b"int main(void) { return 0; }\n"
    )
    service = SourceCodeCheckService(
        catalog_factory=SourceCodeCheckCatalogFactory(),
    )

    result = service.execute(source_code_bytes=source_code_bytes)

    function_check_ids = {
        ("process", "system"),
        ("process", "create_process"),
    }
    assert not function_check_ids.intersection(
        (finding.group_id, finding.check_id) for finding in result.findings
    )


def test_source_code_check_detects_dangerous_string_literals() -> None:
    """コメントではなく文字列リテラルにある危険なコマンドを検出する。"""
    source_code_bytes = (
        b"// cmd.exe must not be detected here.\n"
        b"const char *command = \"cmd.exe /c taskkill /f\";\n"
    )
    service = SourceCodeCheckService(
        catalog_factory=SourceCodeCheckCatalogFactory(),
    )

    result = service.execute(source_code_bytes=source_code_bytes)
    finding_ids = {
        (finding.group_id, finding.check_id)
        for finding in result.findings
    }

    assert ("dangerous_string", "command_interpreter") in finding_ids
    assert ("dangerous_string", "destructive_command") in finding_ids


def test_source_code_check_detects_preprocessor_rules() -> None:
    """外部include、マクロinclude、pragmaを個別の規則として検出する。"""
    source_code_bytes = (
        b"#define HEADER <stdio.h>\n"
        b"#include HEADER\n"
        b"#include \"../secret.h\"\n"
        b"#pragma comment(lib, \"user32.lib\")\n"
    )
    service = SourceCodeCheckService(
        catalog_factory=SourceCodeCheckCatalogFactory(),
    )

    result = service.execute(source_code_bytes=source_code_bytes)
    finding_ids = {
        (finding.group_id, finding.check_id)
        for finding in result.findings
    }

    assert ("preprocessor", "macro_include") in finding_ids
    assert ("preprocessor", "external_include") in finding_ids
    assert ("preprocessor", "pragma_comment") in finding_ids


def test_source_code_check_detects_formatted_file_io() -> None:
    """追加した標準ライブラリのファイル入出力呼び出しを検出する。"""
    source_code_bytes = (
        b"void use_file(FILE *file) {\n"
        b"    fprintf(file, \"value=%d\", 1);\n"
        b"    fscanf(file, \"%d\", &value);\n"
        b"}\n"
    )
    service = SourceCodeCheckService(
        catalog_factory=SourceCodeCheckCatalogFactory(),
    )

    result = service.execute(source_code_bytes=source_code_bytes)
    finding_ids = {
        (finding.group_id, finding.check_id)
        for finding in result.findings
    }

    assert ("file", "write") in finding_ids
    assert ("file", "read") in finding_ids


def test_source_code_check_rejects_non_utf8_source() -> None:
    """UTF-8へ正規化されていないコンパイル対象を検査エラーにする。"""
    service = SourceCodeCheckService(
        catalog_factory=SourceCodeCheckCatalogFactory(),
    )

    with pytest.raises(SourceCodeCheckDecodeError):
        service.execute(source_code_bytes=b"\x82\xa0")


def test_every_function_and_string_rule_can_detect_its_target() -> None:
    """すべての関数呼び出し規則と危険文字列規則が検出可能であることを確認する。"""
    catalog = SourceCodeCheckCatalogFactory().create()
    service = SourceCodeCheckService(
        catalog_factory=SourceCodeCheckCatalogFactory(),
    )

    for group in catalog.groups:
        for entry in group.entries:
            target = entry.target_strings[0]
            if entry.match_type == SourceCodeCheckMatchType.FUNCTION_CALL:
                source_code_text = f"void probe(void) {{ {target}(); }}"
            elif entry.match_type == SourceCodeCheckMatchType.STRING_LITERAL:
                escaped_target = target.replace("\\", "\\\\").replace('"', '\\"')
                source_code_text = f'const char *probe = "{escaped_target}";'
            else:
                continue

            result = service.execute(
                source_code_bytes=source_code_text.encode("utf-8"),
            )
            assert (group.group_id, entry.check_id) in {
                (finding.group_id, finding.check_id)
                for finding in result.findings
            }, (group.group_id, entry.check_id)


def test_source_code_check_detects_suspicious_infinite_loops() -> None:
    """空白表記が異なる代表的な無限ループ構文を検出する。"""
    service = SourceCodeCheckService(
        catalog_factory=SourceCodeCheckCatalogFactory(),
    )

    result = service.execute(
        source_code_bytes=b"while ( 1 ) {}\nfor ( ; ; ) {}\n",
    )

    loop_findings = [
        finding
        for finding in result.findings
        if finding.group_id == "common_c"
        and finding.check_id == "suspicious_loop"
    ]
    assert [finding.line_number for finding in loop_findings] == [1, 2]


def test_compile_checks_actual_source_before_running_compiler() -> None:
    """COMPILEが配置済みソースを検査してからコンパイラを呼ぶことを確認する。"""
    call_order: list[str] = []
    source_code_bytes = b"int main(void) { return 0; }"
    storage_id = Mock()

    storage_create_service = Mock()
    storage_create_service.execute.return_value = storage_id
    storage_load_student_source_service = Mock()
    storage_load_student_source_service.execute.return_value = source_code_bytes
    storage_store_student_executable_service = Mock()
    source_code_check_service = Mock()

    def record_check(**_: object) -> None:
        """静的安全性チェックが呼ばれた順序を記録する。"""
        call_order.append("check")

    source_code_check_service.execute.side_effect = record_check
    storage_run_compiler_service = Mock()

    def run_compiler(**_: object) -> StorageCompileServiceResult:
        """呼び出し順を記録して、コンパイル成功相当の結果を返す。"""
        call_order.append("compile")
        return StorageCompileServiceResult(output="")

    storage_run_compiler_service.execute.side_effect = run_compiler
    storage_delete_service = Mock()
    student_put_stage_result_service = Mock()

    usecase = StudentRunCompileStageUseCase(
        storage_create_service=storage_create_service,
        storage_load_student_source_service=storage_load_student_source_service,
        storage_store_student_executable_service=storage_store_student_executable_service,
        source_code_check_service=source_code_check_service,
        storage_run_compiler_service=storage_run_compiler_service,
        storage_delete_service=storage_delete_service,
        student_put_stage_result_service=student_put_stage_result_service,
    )

    student_id = StudentID("00A0000000A")
    usecase.execute(
        student_id=student_id,
        stage_path=Mock(),
    )

    assert call_order == ["check", "compile"]
    source_code_check_service.execute.assert_called_once_with(
        source_code_bytes=source_code_bytes,
    )
    storage_delete_service.execute.assert_called_once_with(storage_id)


def test_storage_load_student_source_returns_loaded_bytes() -> None:
    """一時ストレージへ配置したソースコードと同じバイト列を返すことを確認する。"""
    source_code_bytes = b"int main(void) { return 0; }"
    student_source_repo = Mock()
    student_source_repo.get.return_value = SourceFileItem(
        content_bytes=source_code_bytes,
        encoding="utf-8",
    )
    storage = Mock()
    storage.files = {}
    storage_repo = Mock()
    storage_repo.get.return_value = storage
    service = StorageLoadStudentSourceService(
        student_source_repo=student_source_repo,
        storage_repo=storage_repo,
    )

    loaded_bytes = service.execute(
        student_id=StudentID("00A0000000A"),
        storage_id=Mock(),
        file_relative_path=Path("main.c"),
    )

    assert loaded_bytes == source_code_bytes
    assert storage.files[Path("main.c")] == source_code_bytes
    storage_repo.put.assert_called_once_with(storage)
