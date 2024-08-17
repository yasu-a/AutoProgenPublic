import os
import re
from datetime import datetime

import openpyxl
from openpyxl.cell.read_only import EmptyCell
from openpyxl.worksheet.worksheet import Worksheet

from app_logging import create_logger


class _ScoreExporterExcelError(RuntimeError):
    pass


class _WorkSheetReader:
    def __init__(self, sheet: Worksheet):
        self._ws = sheet
        self._rows_str = tuple(self._ws.values)

    def get_i_row_table_header(self) -> int:
        for i_row, row in enumerate(self._rows_str):
            if row[0] is not None and row[0].strip().startswith("#"):
                return i_row
        raise _ScoreExporterExcelError("ワークシートのヘッダー行が見つかりません")

    def get_i_row_table_begin(self) -> int:
        return self.get_i_row_table_header() + 1

    def get_i_row_table_end(self) -> int:  # exclusive
        i_row = self.get_i_row_table_begin()
        while i_row < len(self._rows_str):
            if not self.is_student_row(i_row):
                break
            i_row += 1
        return i_row

    def is_student_row(self, i_row) -> bool:
        row = self._rows_str[i_row]
        if row[0] is None:
            return False
        return re.fullmatch(r"\d{2}[A-Z]\d{7}[A-Z]", row[0].strip()) is not None

    def get_student_id_of_row(self, i_row):
        assert self.is_student_row(i_row), self._rows_str[i_row]
        return self._rows_str[i_row][0].strip()

    def find_i_row_of_student_id(self, student_id: str):
        for i_row in range(self.get_i_row_table_begin(), self.get_i_row_table_end()):
            student_id_of_row = self.get_student_id_of_row(i_row)
            if student_id == student_id_of_row:
                return i_row
        raise _ScoreExporterExcelError(
            f"ワークシートに学籍番号{student_id}の行が見つかりません"
        )

    def get_i_column_target(self, target_number: int):
        header = self._rows_str[self.get_i_row_table_header()]
        for i_column, title in enumerate(header):
            if title.strip() == f"問{target_number}":
                return i_column
        raise _ScoreExporterExcelError(f"ワークシートに問{target_number}の列が見つかりません")

    def validate(self):
        header = self._rows_str[self.get_i_row_table_header()]
        if header[0] != "# 学籍番号" \
                or header[1] != "# 氏名" \
                or header[2] != "# 合計点" \
                or header[3] != "問1":
            raise _ScoreExporterExcelError("このワークシートの形式には対応していません", header)

    def create_index_mapping(self, student_ids: list[str], target_number: int) \
            -> dict[str, tuple[int, int]]:  # i_row, i_column
        index_mapping: dict[str, tuple[int, int]] = {}
        i_column_target = self.get_i_column_target(target_number)
        for student_id in student_ids:
            i_row = self.find_i_row_of_student_id(student_id)
            index = i_row, i_column_target
            index_mapping[student_id] = index
        return index_mapping


class ScoreExporter:
    _logger = create_logger()

    def __init__(self, *, student_ids: list[str]):
        self._student_ids = student_ids

        self._excel_path: str | None = None
        self._worksheet_name: str | None = None
        self._target_number: int | None = None
        self._scores: dict[str, int] | None = None  # student-id -> score

    def set_excel_path(self, excel_path):
        self._logger.debug(f"Workbook path set: {excel_path}")
        self._excel_path = excel_path

    def list_valid_worksheet_names(self) -> list[str]:
        wb = openpyxl.open(self._excel_path, read_only=True)
        try:
            ws_name_lst = []
            for ws_name in wb.get_sheet_names():
                if re.fullmatch(r"第\d+回", ws_name) is None:
                    self._logger.exception(f"Invalid worksheet name: {ws_name}")
                    continue
                ws: Worksheet = wb.get_sheet_by_name(ws_name)
                try:
                    _WorkSheetReader(ws).validate()
                except _ScoreExporterExcelError:
                    self._logger.exception(f"Invalid worksheet: {ws_name}")
                    continue
                else:
                    self._logger.debug(f"Valid worksheet: {ws_name}")
                    ws_name_lst.append(ws_name)
            return ws_name_lst
        finally:
            wb.close()

    def set_worksheet_name(self, worksheet_name):
        self._logger.debug(f"Worksheet name set: {worksheet_name}")
        self._worksheet_name = worksheet_name

    def set_target_number(self, target_number: int):
        self._logger.debug(f"Target number set: {target_number}")
        self._target_number = target_number

    def set_scores(self, scores: dict[str, int]):
        self._logger.debug(f"Scores set: {scores}")
        self._scores = scores

    def has_data(self):
        wb = openpyxl.open(self._excel_path, read_only=True)
        try:
            ws = wb.get_sheet_by_name(self._worksheet_name)
            reader = _WorkSheetReader(ws)
            index_mapping: dict[str, tuple[int, int]] \
                = reader.create_index_mapping(self._student_ids, self._target_number)
            for student_id, score in self._scores.items():
                i_row, i_column = index_mapping[student_id]
                cell = ws.cell(row=i_row + 1, column=i_column + 1)
                if not isinstance(cell, EmptyCell):
                    return True
            return False
        finally:
            wb.close()

    def commit(self):
        assert self._excel_path is not None
        assert self._worksheet_name is not None
        assert self._target_number is not None
        assert self._scores is not None

        wb = openpyxl.open(self._excel_path, read_only=False)
        try:
            timestamp = re.sub(r"[-:]", "", str(datetime.now())[:-7]).replace(" ", "-")
            wb.save(os.path.join(self._excel_path) + f"-backup-{timestamp}.xlsx")

            ws = wb.get_sheet_by_name(self._worksheet_name)
            reader = _WorkSheetReader(ws)
            index_mapping: dict[str, tuple[int, int]] \
                = reader.create_index_mapping(self._student_ids, self._target_number)
            for student_id, score in self._scores.items():
                i_row, i_column = index_mapping[student_id]
                if score < 0:
                    continue
                # noinspection PyTypeChecker
                ws.cell(row=i_row + 1, column=i_column + 1, value=score)

            try:
                wb.save(self._excel_path)
            except PermissionError:
                raise _ScoreExporterExcelError(
                    "書き込みを拒否されました。ファイルをExcelで開いていませんか？")
        finally:
            wb.close()
