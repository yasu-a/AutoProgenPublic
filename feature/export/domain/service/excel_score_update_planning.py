"""
Excel点数更新計画サービスの実装
"""
from feature.export.domain.interface.service import (
    IExcelScoreUpdatePlanningService,
    ExcelScoreUpdatePlanningError,
    StudentNameMismatchError,
    InvalidStudentIdError,
)
from feature.export.domain.model.excel_layout import ExcelColumnMapping, ExcelRowRange
from feature.export.domain.model.data import StudentScoreData
from shared.domain.value.excel_cell_table import ExcelCellTable
from shared.domain.value.identifier import StudentID


class ExcelScoreUpdatePlanningService(IExcelScoreUpdatePlanningService):
    """Excel点数更新計画サービスの実装"""

    def execute(
        self,
        *,
        excel_cell_table: ExcelCellTable,
        student_score_map: dict[StudentID, StudentScoreData],
        column_mapping: ExcelColumnMapping,
        row_range: ExcelRowRange,
    ) -> dict[tuple[int, int], int | None]:
        """
        Excelの現状データと正解データを突き合わせ、更新内容を計算する
        """
        update_values: dict[tuple[int, int], int | None] = {}
        errors: list[ExcelScoreUpdatePlanningError] = []

        start_row = row_range.start_row_index
        end_row = row_range.end_row_index
        id_col = column_mapping.student_id_column_index
        name_col = column_mapping.student_name_column_index
        score_col = column_mapping.score_write_column_index

        for r in range(start_row, end_row + 1):  # end_rowは含む
            # 学籍番号読み取り
            id_val = excel_cell_table.get_cell(r, id_col).strip()
            if not id_val:
                continue

            # 学籍番号の検証
            try:
                s_id = StudentID(id_val)
            except ValueError:
                errors.append(InvalidStudentIdError(row_index=r, value=id_val))
                continue

            # 採点データがない場合はスキップ
            if s_id not in student_score_map:
                continue

            # 氏名読み取りと検証
            excel_name = excel_cell_table.get_cell(r, name_col).strip()
            student_score_data = student_score_map[s_id]

            if excel_name != student_score_data.name:
                errors.append(
                    StudentNameMismatchError(
                        student_id=s_id,
                        row_index=r,
                        excel_name=excel_name,
                        expected_name=student_score_data.name,
                    )
                )
                continue  # 氏名が一致しない場合はスキップ

            # 点数書き込み（未採点の場合はNone）
            update_values[(r, score_col)] = student_score_data.score

        # エラーがある場合は例外を発生
        if errors:
            if len(errors) == 1:
                raise errors[0]
            else:
                error_messages = [str(e) for e in errors]
                error_message = "以下のエラーが検出されました:\n" + "\n".join(error_messages)
                raise ExcelScoreUpdatePlanningError(error_message) from errors[0]

        return update_values

