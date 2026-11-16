"""採点結果の確定状態がExcel出力の従来仕様に影響しないことを検証する。"""

from pathlib import Path

import openpyxl

from autoprogen.domain.model.student_mark import StudentMark
from autoprogen.domain.model.value import StudentID, TargetID
from autoprogen.infra.io.score_excel import ScoreExcelIO


def test_unconfirmed_scores_are_still_exported(tmp_path: Path) -> None:
    """未確定でも入力済みの点数を出力し、未採点は空欄にする。"""
    first = StudentID("21D5109047B")
    second = StudentID("24A0007521M")
    third = StudentID("25D5203184K")
    excel_path = tmp_path / "scores.xlsx"
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.append(["# 学籍番号", "# 氏名", "# 合計点", "問1"])
    for student_id in (first, second, third):
        worksheet.append([str(student_id), "試験用", None, None])
    workbook.save(excel_path)
    workbook.close()

    io = ScoreExcelIO(excel_fullpath=excel_path)
    io.apply(
        worksheet_name=worksheet.title,
        student_marks=[
            StudentMark(first, 50, confirmed=False),
            StudentMark(second, 0, confirmed=False),
            StudentMark(third, None),
        ],
        target_id=TargetID(1),
        do_backup=False,
    )

    result = openpyxl.load_workbook(excel_path)
    try:
        sheet = result.active
        assert sheet.cell(row=2, column=4).value == 50
        assert sheet.cell(row=3, column=4).value == 0
        assert sheet.cell(row=4, column=4).value in (None, "")
    finally:
        result.close()
