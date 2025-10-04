import os

from domain.model.value import StudentID
from infra.path_provider.current_project import StudentSubmissionPathProvider


class StudentFolderShowInExplorerIO:
    # 生徒の各種フォルダをエクスプローラで開く

    def __init__(
            self,
            *,
            student_submission_path_provider: StudentSubmissionPathProvider,
    ):
        self._student_submission_path_provider = student_submission_path_provider

    def show_submission_folder(self, student_id: StudentID) -> None:
        # 生徒の提出フォルダをエクスプローラで開く
        submission_folder_fullpath \
            = self._student_submission_path_provider.student_submission_folder_fullpath(student_id)
        if submission_folder_fullpath.exists():
            os.startfile(submission_folder_fullpath)
