from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DecodedContent:
    """バイト列を表示用文字列へ変換した結果を保持する。"""

    # UTF-8としてデコードした文字列、または不正なバイトをエスケープした表示用文字列。
    text: str
    # 元のバイト列全体が正しいUTF-8であったか。
    is_valid_utf8: bool
