from pathlib import PurePosixPath

from domain.error import ManabaReportListParserError
from domain.model.manaba_report_list import ManabaReportList, ManabaReportListRow
from domain.model.readonly_excel_worksheet import ReadonlyExcelWorksheet
from domain.model.value import StudentID


class ManabaReportListParser:
    # manaba reportlist ヘッダーが含むべきラベル群。
    EXPECTED_HEADER_JP_CONTAINS = [
        "内部コースID",
        "コース名",
        "リンク情報",
        "ロール",
        "ユーザID",
        "学籍番号",
        "氏名",
        "氏名（英語）",
        "メールアドレス",
        "合計点",
        "評価",
        "講評",
        "提出",
        "提出日時",
        "提出回数",
        "フォルダ",
    ]

    # reportlist の列インデックス定義。
    IDX_ROLE = 3
    IDX_STUDENT_ID = 5
    IDX_NAME = 6
    IDX_NAME_EN = 7
    IDX_EMAIL = 8
    IDX_SUBMITTED_AT = 13
    IDX_NUM_SUBMISSIONS = 14
    IDX_SUBMISSION_FOLDER = 15

    def _find_row_begin(self, *, worksheet: ReadonlyExcelWorksheet) -> int:
        # manaba の既知フォーマットではテーブル開始行は 8 行目固定。
        for i_row in range(worksheet.row_count()):
            cell_text = worksheet.cell_at(row_index=i_row, column_index=0).text.strip()
            if cell_text and not cell_text.startswith("#"):
                if i_row != 7:
                    raise ManabaReportListParserError(reason="テーブルの開始行が8行目ではありません")
                return i_row
        raise ManabaReportListParserError(reason="テーブルの開始行が見つかりません")

    def _find_row_end(self, *, worksheet: ReadonlyExcelWorksheet, row_begin: int) -> int:
        # #end 行を探索し、テーブル終端を返す。
        for i_row in range(worksheet.row_count()):
            if worksheet.cell_at(row_index=i_row, column_index=0).text.strip() == "#end":
                if i_row <= row_begin:
                    raise ManabaReportListParserError(reason="テーブルの終了行が開始行の前にあります")
                return i_row
        raise ManabaReportListParserError(reason="テーブルの終了行が見つかりません")

    def _validate_header(self, *, worksheet: ReadonlyExcelWorksheet, row_begin: int) -> None:
        # ヘッダー行が想定ラベルを含んでいるか検証する。
        header_row = row_begin - 1
        for i_col, expected_contains in enumerate(self.EXPECTED_HEADER_JP_CONTAINS):
            actual = worksheet.cell_at(row_index=header_row, column_index=i_col).text
            if expected_contains not in actual:
                raise ManabaReportListParserError(
                    reason="不明な形式のヘッダーです。"
                           f"ヘッダーは{'・'.join(self.EXPECTED_HEADER_JP_CONTAINS)}を含んでいる必要があります。",
                )

    @staticmethod
    def _parse_submission_folder_path(*, hyperlink_target: str) -> PurePosixPath:
        # 既存互換: リンク先末尾 "\" を要求し、内部表現は Posix 形式へ寄せる。
        if not hyperlink_target.endswith("\\"):
            raise ManabaReportListParserError(
                reason=f"不明な形式のフォルダパスです: {hyperlink_target}",
            )
        normalized = hyperlink_target.rstrip("\\").replace("\\", "/")
        return PurePosixPath(normalized)

    def parse_worksheet(self, *, worksheet: ReadonlyExcelWorksheet) -> ManabaReportList:
        # ワークシート全体を検証し、履修生行のみの ManabaReportList を構築する。
        row_begin = self._find_row_begin(worksheet=worksheet)
        row_end = self._find_row_end(worksheet=worksheet, row_begin=row_begin)
        self._validate_header(worksheet=worksheet, row_begin=row_begin)

        rows: list[ManabaReportListRow] = []
        for i_row in range(row_begin, row_end):
            role = worksheet.cell_at(row_index=i_row, column_index=self.IDX_ROLE).text
            if role not in ["履修生", "担当教員"] and not role.startswith("授業補助者"):
                raise ManabaReportListParserError(reason=f"不明なロールです: {role}")
            if role != "履修生":
                continue

            student_id_text = worksheet.cell_at(row_index=i_row, column_index=self.IDX_STUDENT_ID).text
            try:
                student_id = StudentID(student_id_text)
            except ValueError:
                raise ManabaReportListParserError(reason=f"不明な形式の学籍番号です: {student_id_text}")

            folder_cell = worksheet.cell_at(row_index=i_row, column_index=self.IDX_SUBMISSION_FOLDER)
            if folder_cell.hyperlink_target is None:
                # リンクなし + 空文字だけを未提出として許可する。
                if folder_cell.text != "":
                    raise ManabaReportListParserError(
                        reason=f"不明な形式の「フォルダ」列です: {folder_cell.text}",
                    )
                is_submitted = False
                folder_path = None
            else:
                # 表示文字は揺れる可能性があるため、主判定は hyperlink の有無で行う。
                if folder_cell.text not in ["", "開く"]:
                    raise ManabaReportListParserError(
                        reason=f"不明な形式の「フォルダ」列です: {folder_cell.text}",
                    )
                is_submitted = True
                folder_path = self._parse_submission_folder_path(
                    hyperlink_target=folder_cell.hyperlink_target,
                )

            rows.append(
                ManabaReportListRow(
                    student_id=student_id,
                    name=worksheet.cell_at(row_index=i_row, column_index=self.IDX_NAME).text,
                    name_en=worksheet.cell_at(row_index=i_row, column_index=self.IDX_NAME_EN).text,
                    email_address=worksheet.cell_at(row_index=i_row, column_index=self.IDX_EMAIL).text,
                    is_submitted=is_submitted,
                    submitted_at_text=worksheet.cell_at(row_index=i_row, column_index=self.IDX_SUBMITTED_AT).text,
                    num_submissions_text=worksheet.cell_at(row_index=i_row, column_index=self.IDX_NUM_SUBMISSIONS).text,
                    submission_folder_path=folder_path,
                )
            )

        return ManabaReportList(rows=tuple(rows))
