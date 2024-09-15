import functools
import re
import shutil
from pathlib import Path

import dateutil.parser
import openpyxl
import pandas as pd

from app_logging import create_logger
from domain.errors import ManabaReportArchiveIOError, ProjectCreateServiceError
from domain.models.project_config import ProjectConfig
from domain.models.student_master import StudentMaster, Student
from domain.models.values import TargetID, ProjectName, StudentID
from files.progress import ProgressIO
from files.project import ProjectIO
from files.project_path_provider import ProjectPathProvider, StudentReportPathProvider
from files.report_archive import ManabaReportArchiveIO
from files.testcase import TestCaseIO


# from services.compiler import StudentEnvCompiler
# from services.importer import StudentSubmissionImporter
# from services.tester import StudentEnvironmentTester


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


class ProjectCreateService:  # TODO: サービスがI/Oに依存している
    def __init__(
            self,
            *,
            project_path_provider: ProjectPathProvider,
            student_report_path_provider: StudentReportPathProvider,
            project_io: ProjectIO,
            manaba_report_archive_io: ManabaReportArchiveIO,
    ):
        self._project_path_provider = project_path_provider
        self._student_report_path_provider = student_report_path_provider
        self._project_io = project_io
        self._manaba_report_archive_io = manaba_report_archive_io

    def create_project(
            self,
            target_id: TargetID,
    ) -> None:
        # create project folder
        self._project_io.create_project_folder()

        # create student master
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
            raise ProjectCreateServiceError(
                reason=f"マスターデータの構成中にエラーが発生しました。\n{e.reason}",
            )
        else:
            self._project_io.write_student_master(student_master)
        finally:
            wb.close()

        # read student master file and create mapping from student_id to submission folder name
        student_master = self._project_io.read_student_master()
        student_id_to_submission_folder_name_mapping: dict[StudentID, str] = {}
        for student in student_master:
            if student.submission_folder_name is not None:
                student_id_to_submission_folder_name_mapping[student.student_id] \
                    = student.submission_folder_name

        # extract student submissions
        try:
            for student_id, student_submission_folder_name in \
                    student_id_to_submission_folder_name_mapping.items():
                self._manaba_report_archive_io.validate_archive_contents(
                    student_submission_folder_names=set(
                        student_id_to_submission_folder_name_mapping.values()
                    ),
                )
                it = self._manaba_report_archive_io.iter_student_submission_archive_contents(
                    student_id=student_id,
                    student_submission_folder_name=student_submission_folder_name,
                )
                submission_extraction_folder_fullpath \
                    = self._student_report_path_provider.submission_folder_fullpath(student_id)
                submission_extraction_folder_fullpath.mkdir(parents=True, exist_ok=False)
                for content_relative_path, fp in it:
                    dst_fullpath = submission_extraction_folder_fullpath / content_relative_path
                    # パスにスペースが含まれているとこの先のos.makedirsで失敗するので取り除く
                    dst_fullpath = Path(*map(str.strip, dst_fullpath.parts))
                    dst_fullpath = dst_fullpath.resolve()
                    assert dst_fullpath.parent.is_relative_to(
                        submission_extraction_folder_fullpath
                    ), dst_fullpath
                    dst_fullpath.parent.mkdir(parents=True, exist_ok=True)
                    with dst_fullpath.open(mode="wb") as f_dst:
                        shutil.copyfileobj(fp, f_dst)
        except ManabaReportArchiveIOError as e:
            raise ProjectCreateServiceError(
                reason=f"ZIPアーカイブの展開中にエラーが発生しました。\n{e.reason}",
            )

        # create project config
        self._project_io.write_config(
            project_config=ProjectConfig(
                target_id=target_id,
            )
        )


class ProjectService:  # TODO: ProgressServiceを分離する
    _logger = create_logger()

    def __init__(
            self,
            *,
            project_io: ProjectIO,
            testcase_io: TestCaseIO,
            progress_io: ProgressIO,
    ):
        self._project_io = project_io
        self._testcase_io = testcase_io
        self._progress_io = progress_io

    def get_project_name(self) -> ProjectName:
        return self._project_io.get_project_name()

    def get_target_id(self) -> TargetID:
        return self._project_io.get_target_id()

    def get_student_ids(self) -> list[StudentID]:
        return [student.student_id for student in self._project_io.students]

    def has_student_submission_folder(self, student_id: StudentID) -> bool:
        return self._project_io.has_student_submission_folder(student_id)

    def show_student_submission_folder_in_explorer(self, student_id: StudentID) -> None:
        self._project_io.show_student_submission_folder_in_explorer(student_id)

    def get_student_meta(self, student_id: StudentID) -> Student:
        return self._project_io.students[student_id]
