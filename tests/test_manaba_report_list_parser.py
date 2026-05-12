from pathlib import PurePosixPath

from domain.model.readonly_excel_worksheet import ReadonlyExcelWorksheet, ReadonlyExcelCell
from service.manaba_report_list_parser import ManabaReportListParser


def test_manaba_report_list_parser_parse_success():
    rows: list[tuple[ReadonlyExcelCell, ...]] = []
    for _ in range(6):
        rows.append((ReadonlyExcelCell("", None),))
    rows.append((ReadonlyExcelCell("#comment", None),))
    rows.append(tuple(
        ReadonlyExcelCell(text, None)
        for text in [
            "1",
            "course",
            "link",
            "履修生",
            "uid",
            "21D5109047B",
            "範馬　刃牙",
            "HANMA Baki",
            "a@example.com",
            "",
            "",
            "",
            "提出",
            "2026-04-17 16:56:13",
            "1",
            "開く",
        ]
    ))
    rows.append(tuple(
        ReadonlyExcelCell(text, None)
        for text in [
            "1",
            "course",
            "link",
            "履修生",
            "uid2",
            "26HJ403216F",
            "烈　海王",
            "RETSU Kaioh",
            "b@example.com",
            "",
            "",
            "",
            "未提出",
            "",
            "",
            "",
        ]
    ))
    rows.append((ReadonlyExcelCell("#end", None),))

    # header row at 7th row (index=6)
    header = (
        "#内部コースID", "コース名", "リンク情報", "ロール", "ユーザID", "学籍番号",
        "氏名", "氏名（英語）", "メールアドレス", "合計点", "評価", "講評",
        "提出", "提出日時", "提出回数", "フォルダ",
    )
    rows[6] = tuple(ReadonlyExcelCell(text, None) for text in header)

    # data row at 8th row (index=7)
    data = list(rows[7])
    data[15] = ReadonlyExcelCell("開く", "21D5109047B@21D5109047B\\")
    rows[7] = tuple(data)

    worksheet = ReadonlyExcelWorksheet(rows=tuple(rows))
    parser = ManabaReportListParser()

    report_list = parser.parse_worksheet(worksheet=worksheet)
    assert report_list.row_count() == 2

    # TODO: check other important fields
    row0 = report_list.get_row(row_index=0)
    assert str(row0.student_id) == "21D5109047B"
    assert row0.is_submitted
    assert row0.submission_folder_path == PurePosixPath("21D5109047B@21D5109047B")

    row1 = report_list.get_row(row_index=1)
    assert str(row1.student_id) == "26HJ403216F"
    assert not row1.is_submitted
    assert row1.submission_folder_path is None
