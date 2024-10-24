import os

from domain.models.values import StudentID
from files.path_providers.current_project import ReportSubmissionPathProvider


class StudentFolderShowInExplorerIO:
    # 生徒の各種フォルダをエクスプローラで開く

    def __init__(
            self,
            *,
            report_submission_path_provider: ReportSubmissionPathProvider,
    ):
        self._report_submission_path_provider = report_submission_path_provider

    def show_submission_folder(self, student_id: StudentID) -> None:
        # 生徒の提出フォルダをエクスプローラで開く
        submission_folder_fullpath \
            = self._report_submission_path_provider.student_submission_folder_fullpath(student_id)
        if submission_folder_fullpath.exists():
            os.startfile(submission_folder_fullpath)
