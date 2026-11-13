"""保存済みのエラーメッセージから安全性チェックの表示情報を読み取る。"""

import re
from collections.abc import Sequence
from dataclasses import dataclass

from autoprogen.usecase.dto.student_table_cell_data import StudentErrorCellDataTextEntry


SAFETY_ERROR_PREFIX = (
    "ソースコードの安全性チェックで問題が検出されたため、"
    "コンパイルを停止しました。"
)
_SHA_PATTERN = re.compile(r"(?m)^検査対象SHA-256: ([0-9a-f]{64})$")
_LINE_PATTERN = re.compile(r"(?m)^(\d+)行目: \[[A-Za-z0-9_]+\.[A-Za-z0-9_]+\]")


@dataclass(frozen=True)
class SourceSafetyErrorDetails:
    """専用ウィジェットが必要とする検査時の情報。"""

    source_sha256: str | None
    line_numbers: tuple[int, ...]


def parse_safety_check_error(
        entries: Sequence[StudentErrorCellDataTextEntry],
) -> SourceSafetyErrorDetails | None:
    """安全性チェックに固有のメッセージだけを認識する。"""
    matched_messages = [
        entry.summary_text
        for entry in entries
        if entry.summary_text.startswith(SAFETY_ERROR_PREFIX)
    ]
    if not matched_messages:
        return None

    # 複数のステージパスから同じエラーが来ても重複を除く。
    messages = set(matched_messages)
    hashes = {
        match.group(1)
        for message in messages
        for match in _SHA_PATTERN.finditer(message)
    }
    # 検査時のハッシュが欠落または競合している場合は許可できない。
    source_sha256 = next(iter(hashes)) if len(hashes) == 1 and all(
        len(_SHA_PATTERN.findall(message)) == 1 for message in messages
    ) else None
    line_numbers = tuple(sorted({
        int(match.group(1))
        for message in messages
        for match in _LINE_PATTERN.finditer(message)
        if int(match.group(1)) > 0
    }))
    return SourceSafetyErrorDetails(
        source_sha256=source_sha256,
        line_numbers=line_numbers,
    )
