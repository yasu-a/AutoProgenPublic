import dateutil.parser

from domain.error import StudentMasterServiceError
from domain.model.manaba_report_list import ManabaReportList
from domain.model.student import Student
from infra.repository.student import StudentRepository


class StudentMasterCreateService:  # TODO: StudentService系にモジュールと名称を統合
    def __init__(
            self,
            *,
            student_repo: StudentRepository,
    ):
        self._student_repo = student_repo

    def execute(
            self,
            *,
            report_list: ManabaReportList,
    ) -> None:
        if self._student_repo.exists_any():
            return

        students: list[Student] = []
        try:
            for i in range(report_list.row_count()):
                row = report_list.get_row(row_index=i)
                if row.is_submitted:
                    if row.submission_folder_path is None:
                        raise ValueError("提出済みなのに提出フォルダがありません")
                    # 文字列->型変換の責務はここに残し、失敗は ServiceError に寄せる。
                    submitted_at = dateutil.parser.parse(row.submitted_at_text)
                    num_submissions = int(row.num_submissions_text)
                    submission_folder_name = str(row.submission_folder_path)
                else:
                    # 既存DB互換: 未提出は submitted_at=None, num_submissions=0, folder=None。
                    submitted_at = None
                    num_submissions = 0
                    submission_folder_name = None

                students.append(
                    Student(
                        student_id=row.student_id,
                        name=row.name,
                        name_en=row.name_en,
                        email_address=row.email_address,
                        submitted_at=submitted_at,
                        num_submissions=num_submissions,
                        submission_folder_name=submission_folder_name,
                    )
                )
        except ValueError as e:
            raise StudentMasterServiceError(
                reason=f"マスターデータの構成中にエラーが発生しました。\n{e!s}",
            )

        self._student_repo.create_all(students)
