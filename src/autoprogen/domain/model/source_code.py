import hashlib
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceCode:
    """文字コードと改行コードを正規化したCソースコードを表す。"""

    # 正規化済みのソースコード本文。
    text: str

    def __post_init__(self) -> None:
        """本文が文字列であり、UTF-8へ変換できることを検証する。"""
        if type(self.text) is not str:
            raise TypeError("textはstrである必要があります")

        try:
            self.text.encode("utf-8", errors="strict")
        except UnicodeEncodeError as error:
            raise ValueError("textはUTF-8へ変換できる必要があります") from error

    def to_utf8_bytes(self) -> bytes:
        """正規化済みの本文をUTF-8バイト列として返す。"""
        return self.text.encode("utf-8")

    def calculate_sha256(self) -> str:
        """正規化済みのUTF-8バイト列に対するSHA-256を返す。"""
        return hashlib.sha256(self.to_utf8_bytes()).hexdigest()
