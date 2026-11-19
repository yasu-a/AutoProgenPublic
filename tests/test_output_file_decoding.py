from autoprogen.domain.model.output_file import OutputFile
from autoprogen.domain.model.value import FileID


def test_output_file_decodes_valid_utf8_without_changing_bytes() -> None:
    """正しいUTF-8はそのままデコードし、元のバイト列を維持する。"""
    content = "結果: 42\n".encode("utf-8")
    output_file = OutputFile(file_id=FileID.STDOUT, content=content)

    decoded = output_file.get_decoded_content()

    assert decoded.text == "結果: 42\n"
    assert decoded.is_valid_utf8
    assert output_file.content_bytes == content


def test_output_file_escapes_invalid_utf8_without_changing_bytes() -> None:
    """不正なUTF-8は表示用にエスケープし、元のバイト列を維持する。"""
    content = b"result: \x81\xff\n"
    output_file = OutputFile(file_id=FileID.STDOUT, content=content)

    decoded = output_file.get_decoded_content()

    assert decoded.text == r"result: \x81\xff" + "\n"
    assert not decoded.is_valid_utf8
    assert output_file.content_bytes == content
