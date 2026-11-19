from pathlib import Path

import pytest

from autoprogen.domain.error.stage.compile import CompilerDiagnosticError
from autoprogen.domain.error.stage.test import OutputDecodingError, OutputMatchingError
from autoprogen.domain.model.value import FileID
from autoprogen.domain.service.stage_error_codec import StageErrorCodec, StageErrorRecord


def test_stage_error_codec_roundtrip() -> None:
    """具象エラーをレコードに変換し、元の型と値に復元できることを確認する。"""
    codec = StageErrorCodec()
    error = OutputMatchingError(detail="テスト用エラー")

    record = codec.encode(error)

    assert record == StageErrorRecord(
        error_group_id="test",
        error_type_id="output_matching_error",
        params={"detail": "テスト用エラー"},
    )

    restored = codec.decode(record)

    assert isinstance(restored, OutputMatchingError)
    assert restored.detail == error.detail


def test_compile_error_output_is_not_persisted_by_codec() -> None:
    """コンパイラ生出力をエラーの保存パラメータへ含めないことを確認する。"""
    codec = StageErrorCodec()

    record = codec.encode(CompilerDiagnosticError(output="raw compiler output"))
    restored = codec.decode(record)

    assert record.params == {}
    assert isinstance(restored, CompilerDiagnosticError)
    assert restored.output is None


@pytest.mark.parametrize("file_id", [FileID.STDOUT, FileID(Path("result.bin"))])
def test_output_decoding_error_codec_roundtrip(file_id: FileID) -> None:
    """デコードできなかった出力ファイルの識別子を保存・復元する。"""
    codec = StageErrorCodec()
    error = OutputDecodingError(file_id=file_id)

    record = codec.encode(error)
    restored = codec.decode(record)

    assert record == StageErrorRecord(
        error_group_id="test",
        error_type_id="output_decoding_error",
        params={"file_id": file_id.to_json()},
    )
    assert isinstance(restored, OutputDecodingError)
    assert restored.file_id == file_id
