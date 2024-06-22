# import functools
# import re
#
# import openpyxl
# import pandas as pd
#
#
# class UnexpectedStudentMasterError(ValueError):
#     pass
#
#
# class StudentMasterExcelReader:
#     @staticmethod
#     def __load_worksheet(workbook: openpyxl.Workbook):
#         if len(workbook.worksheets) != 1:
#             raise UnexpectedStudentMasterError(
#                 "ワークブックは1つだけワークシートを含んでいる必要があります"
#             )
#         return workbook.worksheets[0]
#
#     def __init__(self, master_path):
#         self.__ws = self.__load_worksheet(openpyxl.load_workbook(master_path))
#         self.__rows_str = tuple(self.__ws.values)
#
#     @functools.cache
#     def find_row_begin(self) -> int:
#         for i_row, row in enumerate(self.__rows_str):
#             if not row[0].strip().startswith("#"):
#                 if i_row != 7:
#                     raise UnexpectedStudentMasterError(
#                         "テーブルの開始行が8行目ではありません"
#                     )
#                 return i_row
#         raise UnexpectedStudentMasterError(
#             "テーブルの開始行が見つかりません"
#         )
#
#     @functools.cache
#     def find_row_end(self) -> int:
#         for i_row, row in enumerate(self.__rows_str):
#             if row[0].strip() == "#end":
#                 if i_row <= self.find_row_begin():
#                     raise UnexpectedStudentMasterError(
#                         "テーブルの終了行が開始行の前にあります"
#                     )
#                 return i_row
#         raise UnexpectedStudentMasterError(
#             "テーブルの終了行が見つかりません"
#         )
#
#     EXPECTED_HEADER_JP_CONTAINS = [
#         "内部コースID",
#         "コース名",
#         "リンク情報",
#         "ロール",
#         "ユーザID",
#         "学籍番号",
#         "氏名",
#         "氏名（英語）",
#         "メールアドレス",
#         "合計点",
#         "評価",
#         "講評",
#         "提出",
#         "提出日時",
#         "提出回数",
#         "フォルダ",
#     ]
#
#     def get_header(self):
#         return self.__rows_str[self.find_row_begin() - 1]
#
#     def validate_header(self):
#         for col, expected_contains in zip(self.get_header(), self.EXPECTED_HEADER_JP_CONTAINS):
#             if expected_contains not in col:
#                 raise UnexpectedStudentMasterError(
#                     f"ヘッダーの形式が一致しません: \"{expected_contains}\" not in \"{col}\""
#                 )
#
#     HEADER = [
#         "course_id",
#         "course_name",
#         "link_info",
#         "role",
#         "user_id",
#         "student_id",
#         "name",
#         "name_en",
#         "email_address",
#         "grade",
#         "sym_grade",
#         "comment",
#         "submission_state",
#         "submitted_at",
#         "num_submissions",
#         "submission_folder",
#         "row_id",
#     ]
#
#     @functools.cached_property
#     def dataframe(self):
#         self.validate_header()
#         rows = []
#         for i_row in range(self.find_row_begin(), self.find_row_end()):
#             row = self.__rows_str[i_row]
#             row = *row, i_row
#             rows.append(row)
#         return pd.DataFrame(rows, columns=self.HEADER)
#
#     def _validate_roles(self):
#         for role in self.dataframe["role"].value_counts().index:
#             if role in ["履修生", "担当教員"]:
#                 continue
#             if role.startswith("授業補助者"):
#                 continue
#             raise UnexpectedStudentMasterError(
#                 f"不明なロールです: {role}"
#             )
#
#     @functools.cached_property
#     def student_dataframe(self):
#         return self.dataframe.loc[self.dataframe["role"] == "履修生"].copy()
#
#     def _validate_student_ids(self):
#         student_ids = self.student_dataframe["student_id"]
#         for student_id in student_ids:
#             if not re.fullmatch(r"\d{2}[A-Z]\d{7}[A-Z]", student_id):
#                 raise UnexpectedStudentMasterError(
#                     f"不明な形式の学籍番号です: {student_id}"
#                 )
#
#     def validate_table(self):
#         self._validate_roles()
#         self._validate_student_ids()
#
#     def get_student_submission_folder_names(self) -> list[str | None]:
#         submission_folder_names = []
#         for _, row in self.student_dataframe.iterrows():
#             i_row = row["row_id"]
#             submission_folder_cell \
#                 = self.__ws.cell(row=i_row + 1, column=self.HEADER.index("submission_folder") + 1)
#             if submission_folder_cell.value not in ["", "開く"]:
#                 raise UnexpectedStudentMasterError(
#                     f"不明な形式の「フォルダ」列です: {submission_folder_cell.value}"
#                 )
#             if submission_folder_cell.hyperlink is None:
#                 link_path = None
#             else:
#                 link_path = submission_folder_cell.hyperlink.target
#             if link_path is not None and not link_path.endswith("\\"):
#                 raise UnexpectedStudentMasterError(
#                     f"不明な形式のフォルダパスです: {link_path}"
#                 )
#             if link_path is not None:
#                 link_path = link_path.rstrip("\\")
#             submission_folder_names.append(link_path)
#         return submission_folder_names
#
#     def as_dataframe(self):
#         df = self.student_dataframe.copy()
#         df["submission_folder_name"] = self.get_student_submission_folder_names()
#         return df
#
#
# class StudentMasterIO:
#     def __init__(self, *, master_path):
#         self.__master_path = master_path
#         self.__reader = StudentMasterExcelReader(master_path)
#
#     def read_as_dataframe(self):
#         return self.__reader.as_dataframe()
