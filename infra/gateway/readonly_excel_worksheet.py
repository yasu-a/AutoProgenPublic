import io

import openpyxl

from domain.error import ReadonlyExcelWorksheetGatewayError
from domain.model.readonly_excel_worksheet import ReadonlyExcelWorksheet, ReadonlyExcelCell


class ReadonlyExcelWorksheetGateway:
    def read_from_bytes(self, *, excel_bytes: bytes) -> ReadonlyExcelWorksheet:
        # Excel binary を openpyxl で読み込み、ドメイン非依存なセル表へ変換する。
        wb = None
        try:
            # reportlist 形式検証はここでは行わず、純粋に「読み取り専用の表」へ変換する。
            wb = openpyxl.open(io.BytesIO(excel_bytes))
            if len(wb.worksheets) != 1:
                raise ReadonlyExcelWorksheetGatewayError(
                    reason="ワークブックは1つだけワークシートを含んでいる必要があります",
                )
            ws = wb.worksheets[0]
            rows: list[tuple[ReadonlyExcelCell, ...]] = []
            for row in ws.iter_rows():
                cells: list[ReadonlyExcelCell] = []
                for cell in row:
                    # 下流の条件分岐を単純化するため、空セルは必ず "" に正規化する。
                    text = "" if cell.value is None else str(cell.value)
                    hyperlink_target = None
                    if cell.hyperlink is not None and cell.hyperlink.target is not None:
                        hyperlink_target = str(cell.hyperlink.target)
                    cells.append(ReadonlyExcelCell(text, hyperlink_target))
                rows.append(tuple(cells))
            return ReadonlyExcelWorksheet(rows=tuple(rows))
        except ReadonlyExcelWorksheetGatewayError:
            raise
        except Exception as e:
            raise ReadonlyExcelWorksheetGatewayError(
                reason=f"生徒マスタExcelの読み込みに失敗しました。\n{e!s}",
            )
        finally:
            if wb is not None:
                wb.close()
