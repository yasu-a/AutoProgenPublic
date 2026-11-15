import hashlib

import pytest

from autoprogen.domain.model.source_code import SourceCode
from autoprogen.domain.service.source_code_factory import (
    SourceCodeDecodeError,
    SourceCodeFactory,
)


def test_source_code_returns_utf8_bytes_and_sha256() -> None:
    """本文と同じUTF-8バイト列およびSHA-256を返すことを確認する。"""
    source_code = SourceCode(text="int main(void) { return 0; }\n")
    expected_bytes = b"int main(void) { return 0; }\n"

    assert source_code.to_utf8_bytes() == expected_bytes
    assert source_code.calculate_sha256() == hashlib.sha256(expected_bytes).hexdigest()


@pytest.mark.parametrize("encoding", ["utf-8", "shift-jis"])
def test_source_code_factory_decodes_supported_encodings(encoding: str) -> None:
    """UTF-8とShift-JISの入力が同じ正規化結果になることを確認する。"""
    source_code_text = "// 日本語\r\nint main(void) {\r\n    return 0;\r\n}\r\n"

    source_code = SourceCodeFactory().create(source_code_text.encode(encoding))

    assert source_code.text == "// 日本語\nint main(void) {\n    return 0;\n}\n"


def test_source_code_factory_preserves_bom_and_standalone_carriage_return() -> None:
    """現行仕様どおりBOMとCR単独を変更しないことを確認する。"""
    source_code_bytes = "\ufeffa\rb\r\nc\n".encode("utf-8")

    source_code = SourceCodeFactory().create(source_code_bytes)

    assert source_code.text == "\ufeffa\rb\nc\n"
    assert source_code.to_utf8_bytes() == "\ufeffa\rb\nc\n".encode("utf-8")


def test_source_code_factory_rejects_unknown_encoding() -> None:
    """UTF-8とShift-JISのどちらでもない入力を拒否することを確認する。"""
    with pytest.raises(SourceCodeDecodeError):
        SourceCodeFactory().create(b"\xff")


def test_source_code_rejects_text_that_cannot_be_encoded_as_utf8() -> None:
    """UTF-8へ変換できない不正なUnicode文字列を拒否することを確認する。"""
    with pytest.raises(ValueError):
        SourceCode(text="\ud800")
