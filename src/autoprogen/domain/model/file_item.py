from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutableFileItem:
    """コンパイル済みの実行ファイルを表す。"""

    # 実行ファイル本体のバイト列。
    content_bytes: bytes
