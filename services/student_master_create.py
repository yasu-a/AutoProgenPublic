import functools
import re

import dateutil.parser
import openpyxl
import pandas as pd

from domain.errors import ManabaReportArchiveIOError, StudentMasterServiceError
from domain.models.student import Student
from domain.models.student_master import StudentMaster
from domain.models.values import StudentID
from infra.io.report_archive import ManabaReportArchiveIO
from infra.repositories.student import StudentRepository


class _UnexpectedStudentMasterExcelError(RuntimeError):
    def __init__(self, reason: str):
        self.reason = reason


class _StudentMasterExcelReader:
    @staticmethod
    def __load_worksheet(workbook: openpyxl.Workbook):
        if len(workbook.worksheets) != 1:
            raise _UnexpectedStudentMasterExcelError(
                reason="ワークブックは1つだけワークシートを含んでいる必要があります"
            )
        return workbook.worksheets[0]

    def __init__(self, wb: openpyxl.Workbook):
        self.__ws = self.__load_worksheet(wb)
        self.__rows_str = tuple(self.__ws.values)

    @functools.cache
    def find_row_begin(self) -> int:
        for i_row, row in enumerate(self.__rows_str):
            if row[0] is not None and not row[0].strip().startswith("#"):
                if i_row != 7:
                    raise _UnexpectedStudentMasterExcelError(
                        reason="テーブルの開始行が8行目ではありません"
                    )
                return i_row
        raise _UnexpectedStudentMasterExcelError(
            reason="テーブルの開始行が見つかりません"
        )

    @functools.cache
    def find_row_end(self) -> int:
        for i_row, row in enumerate(self.__rows_str):
            if row[0] is not None and row[0].strip() == "#end":
                if i_row <= self.find_row_begin():
                    raise _UnexpectedStudentMasterExcelError(
                        reason="テーブルの終了行が開始行の前にあります"
                    )
                return i_row
        raise _UnexpectedStudentMasterExcelError(
            reason="テーブルの終了行が見つかりません"
        )

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

    def get_header(self):
        return self.__rows_str[self.find_row_begin() - 1]

    def validate_header(self):
        for col, expected_contains in zip(self.get_header(), self.EXPECTED_HEADER_JP_CONTAINS):
            if col is None or expected_contains not in col:
                raise _UnexpectedStudentMasterExcelError(
                    reason=f"不明な形式のヘッダーです。ヘッダーは{'・'.join(self.EXPECTED_HEADER_JP_CONTAINS)}を含んでいる必要があります。"
                )

    HEADER = [
        "course_id",
        "course_name",
        "link_info",
        "role",
        "user_id",
        "student_id",
        "name",
        "name_en",
        "email_address",
        "grade",
        "sym_grade",
        "comment",
        "submission_state",
        "submitted_at",
        "num_submissions",
        "submission_folder",
        "row_id",
    ]

    @functools.cached_property
    def dataframe(self):
        self.validate_header()
        rows = []
        for i_row in range(self.find_row_begin(), self.find_row_end()):
            row = self.__rows_str[i_row]
            row = *row, i_row
            rows.append(row)
        return pd.DataFrame(rows, columns=self.HEADER)

    def _validate_roles(self):
        for role in self.dataframe["role"].value_counts().index:
            if role in ["履修生", "担当教員"]:
                continue
            if role.startswith("授業補助者"):
                continue
            raise _UnexpectedStudentMasterExcelError(
                reason=f"不明なロールです: {role}"
            )

    @functools.cached_property
    def student_dataframe(self):
        return self.dataframe.loc[self.dataframe["role"] == "履修生"].copy()

    def _validate_student_ids(self):
        student_ids = self.student_dataframe["student_id"]
        for student_id in student_ids:
            if not re.fullmatch(r"\d{2}[A-Z]\d{7}[A-Z]", student_id):
                raise _UnexpectedStudentMasterExcelError(
                    reason=f"不明な形式の学籍番号です: {student_id}"
                )

    def validate_table(self):
        self._validate_roles()
        self._validate_student_ids()

    def get_student_submission_folder_names(self) -> list[str | None]:
        submission_folder_names = []
        for _, row in self.student_dataframe.iterrows():
            i_row = row["row_id"]
            submission_folder_cell \
                = self.__ws.cell(row=i_row + 1, column=self.HEADER.index("submission_folder") + 1)
            if submission_folder_cell.value not in ["", "開く"]:
                raise _UnexpectedStudentMasterExcelError(
                    reason=f"不明な形式の「フォルダ」列です: {submission_folder_cell.value}"
                )
            if submission_folder_cell.hyperlink is None:
                link_path = None
            else:
                link_path = submission_folder_cell.hyperlink.target
            if link_path is not None and not link_path.endswith("\\"):
                raise _UnexpectedStudentMasterExcelError(
                    reason=f"不明な形式のフォルダパスです: {link_path}"
                )
            if link_path is not None:
                link_path = link_path.rstrip("\\")
            submission_folder_names.append(link_path)
        return submission_folder_names

    def as_dataframe(self):
        df = self.student_dataframe.copy()
        df["submission_folder_name"] = self.get_student_submission_folder_names()
        return df


class StudentMasterCreateService:  # TODO: StudentService系にモジュールと名称を統合
    def __init__(
            self,
            *,
            student_repo: StudentRepository,
            manaba_report_archive_io: ManabaReportArchiveIO,
    ):
        self._student_repo = student_repo
        self._manaba_report_archive_io = manaba_report_archive_io

    def execute(self):
        if self._student_repo.exists():
            return

        try:
            with self._manaba_report_archive_io.open_master_excel() as f:
                wb = openpyxl.open(
                    f,
                    # read_only=True,  # ハイパーリンクを読み取れなくなる
                )
                df = _StudentMasterExcelReader(wb).as_dataframe()
                student_master = StudentMaster()
                for _, row in df.iterrows():
                    has_submission = row["submission_folder_name"] is not None
                    student = Student(
                        student_id=StudentID(row["student_id"]),
                        name=row["name"],
                        name_en=row["name_en"],
                        email_address=row["email_address"],
                        submitted_at=(
                            dateutil.parser.parse(row["submitted_at"])
                            if has_submission
                            else None
                        ),
                        num_submissions=(
                            int(row["num_submissions"])
                            if has_submission
                            else 0
                        ),
                        submission_folder_name=row["submission_folder_name"],
                    )
                    student_master.append(student)
        except (_UnexpectedStudentMasterExcelError, ManabaReportArchiveIOError) as e:
            raise StudentMasterServiceError(
                reason=f"マスターデータの構成中にエラーが発生しました。\n{e.reason}",
            )
        else:
            self._student_repo.put(student_master)
        finally:
            wb.close()
