from typing import NamedTuple


class ReadonlyExcelCell(NamedTuple):
    # セルの表示テキスト。空セルは "" に正規化して保持する。
    text: str
    # ハイパーリンク先。リンクがない場合は None。
    hyperlink_target: str | None


class ReadonlyExcelWorksheet:
    # 行優先の2次元セル配列。外部から直接変更させない内部表現。
    _rows: tuple[tuple[ReadonlyExcelCell, ...], ...]

    def __init__(
            self,
            *,
            rows: tuple[tuple[ReadonlyExcelCell, ...], ...],
    ):
        # Gateway で生成済みの読み取り専用セル表を受け取って保持する。
        self._rows = rows

    def row_count(self) -> int:
        # 行数を返す。
        return len(self._rows)

    def column_count(self) -> int:
        # すべての行のうち最大列数を返す。
        if not self._rows:
            return 0
        return max(len(row) for row in self._rows)

    def cell_at(
            self,
            *,
            row_index: int,
            column_index: int,
    ) -> ReadonlyExcelCell:
        # 指定位置のセルを返す。行が範囲外なら例外にする。
        if row_index < 0 or row_index >= self.row_count():
            raise IndexError((row_index, self.row_count()))
        row = self._rows[row_index]
        if column_index < 0 or column_index >= len(row):
            # 疎な行を扱いやすくするため、範囲外セルは空セルとして扱う。
            return ReadonlyExcelCell("", None)
        return row[column_index]
