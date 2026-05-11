import os

from domain.model.value import StudentID
from infra.path_layout import ProjectPathLayout


class StudentFolderShowInExplorerIO:
    # 生徒の各種フォルダをエクスプローラで開く

    def __init__(
            self,
            *,
            project_path_layout: ProjectPathLayout,
    ):
        self._project_path_layout = project_path_layout

    def show_submission_folder(self, student_id: StudentID) -> None:
        # 生徒の提出フォルダをエクスプローラで開く
        submission_folder_fullpath = self._project_path_layout.student_submission_dir(student_id)
        if submission_folder_fullpath.exists():
            os.startfile(submission_folder_fullpath)
