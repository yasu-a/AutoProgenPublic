from feature.export.domain.interface.service import (
    IExcelLayoutDetectionService,
    ExcelLayoutDetectionError,
    HeaderRowNotFoundError,
    StudentNameColumnNotFoundError,
    ScoreColumnNotFoundError,
    DataRowNotFoundError,
)
from feature.export.domain.model.excel_layout import ExcelColumnMapping, ExcelRowRange
from shared.domain.value.excel_cell_table import ExcelCellTable
from shared.domain.value.identifier import TargetID, StudentID


class ExcelLayoutDetectionService(IExcelLayoutDetectionService):
    """Excelレイアウト検出サービスの実装"""

    def execute(
        self,
        *,
        excel_cell_table: ExcelCellTable,
        target_id: TargetID,
    ) -> tuple[ExcelColumnMapping, ExcelRowRange]:
        """
        単純なヒューリスティックで列を特定する。
        - "# 学籍番号" または "学籍番号" がある行をヘッダーとする
        - その行にある "問X" をターゲット列とする
        - 学籍番号で埋まっている最後の行を検出する
        
        Raises:
            HeaderRowNotFoundError: ヘッダー行（学籍番号列）が見つからない場合
            StudentNameColumnNotFoundError: 氏名列が見つからない場合
            ScoreColumnNotFoundError: 設問番号列が見つからない場合
            DataRowNotFoundError: データ行が見つからない場合
        """
        if excel_cell_table.is_empty():
            raise HeaderRowNotFoundError()

        # 探索範囲（パフォーマンスのため最初の20行程度を見る）
        rows = excel_cell_table.get_rows()
        if not rows:
            raise HeaderRowNotFoundError()

        # 1. ヘッダー行と学籍番号列の特定
        header_result = self._detect_header_and_student_id_column(excel_cell_table, rows)
        if header_result is None:
            raise HeaderRowNotFoundError()
        header_row_index, student_id_col = header_result

        # 2. 氏名列の特定
        student_name_col = self._detect_student_name_column(excel_cell_table, header_row_index)
        if student_name_col == -1:
            raise StudentNameColumnNotFoundError()

        # 3. 設問番号列の特定
        score_col = self._detect_score_column(excel_cell_table, header_row_index, target_id)
        if score_col == -1:
            raise ScoreColumnNotFoundError(target_id)

        # 4. データ終了行を検出
        start_row = header_row_index + 1
        end_row_index = self._detect_end_row_index(excel_cell_table, rows, start_row, student_id_col)
        if end_row_index < start_row:
            raise DataRowNotFoundError()

        return (
            ExcelColumnMapping(
                student_id_column_index=student_id_col,
                student_name_column_index=student_name_col,
                score_write_column_index=score_col,
            ),
            ExcelRowRange(
                start_row_index=start_row,
                end_row_index=end_row_index,
            )
        )

    def _detect_header_and_student_id_column(
        self,
        excel_cell_table: ExcelCellTable,
        rows: list[int],
    ) -> tuple[int, int] | None:
        """
        ヘッダー行と学籍番号列を検出
        
        Returns:
            (header_row_index, student_id_column_index) または None
        """
        for r in rows[:20]:
            cols = excel_cell_table.get_columns(r)
            for c in cols:
                val = excel_cell_table.get_cell(r, c).strip()
                # 「学籍番号」が含まれているセルを検出
                if "学籍番号" in val:
                    return (r, c)
        return None

    def _detect_student_name_column(
        self,
        excel_cell_table: ExcelCellTable,
        header_row_index: int,
    ) -> int:
        """
        氏名列を検出
        
        Returns:
            氏名列のインデックス（見つからない場合は-1）
        """
        cols = excel_cell_table.get_columns(header_row_index)
        for c in cols:
            val = excel_cell_table.get_cell(header_row_index, c).strip()
            # 「氏名」が含まれているセルを検出
            if "氏名" in val:
                return c
        return -1

    def _detect_score_column(
        self,
        excel_cell_table: ExcelCellTable,
        header_row_index: int,
        target_id: TargetID,
    ) -> int:
        """
        設問番号列を検出
        
        Returns:
            設問番号列のインデックス（見つからない場合は-1）
        """
        target_str = f"問{int(target_id)}"  # "問1" など
        cols = excel_cell_table.get_columns(header_row_index)
        for c in cols:
            val = excel_cell_table.get_cell(header_row_index, c).strip()
            # "問1" や "問1(10点)" などにヒットさせる
            if val == target_str or val.startswith(target_str + "(") or val.startswith(target_str + " "):
                return c
        return -1

    def _detect_end_row_index(
        self,
        excel_cell_table: ExcelCellTable,
        rows: list[int],
        start_row: int,
        student_id_col: int,
    ) -> int:
        """
        データ終了行を検出（学籍番号で埋まっている最後の行）
        
        Returns:
            終了行のインデックス（データがない場合はstart_row - 1）
        """
        end_row_index = start_row - 1  # デフォルトは開始行の前（データなし）
        
        # 学籍番号列が存在する行を探す
        for r in rows:
            if r < start_row:
                continue
            
            # 学籍番号列のセル値を取得
            cell_val = excel_cell_table.get_cell(r, student_id_col).strip()
            if not cell_val:
                # 空のセルが見つかったら、その前の行が終了行
                break
            
            # StudentIDに変換できるか試す
            try:
                StudentID(cell_val)
                end_row_index = r  # 有効な学籍番号が見つかった行を更新
            except ValueError:
                # 学籍番号として無効な値が見つかったら、その前の行が終了行
                break

        return end_row_index
