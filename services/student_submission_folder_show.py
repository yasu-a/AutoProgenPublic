from domain.models.values import StudentID
from files.external.student_folder_show_in_explorer import StudentFolderShowInExplorerIO


class StudentSubmissionFolderShowService:
    # 生徒の提出データが入ったフォルダをエクスプローラで開く

    def __init__(
            self,
            *,
            student_folder_show_in_explorer_io: StudentFolderShowInExplorerIO,
    ):
        self._student_folder_open_in_explorer_io = student_folder_show_in_explorer_io

    def execute(self, student_id: StudentID):
        self._student_folder_open_in_explorer_io.show_submission_folder(student_id)
