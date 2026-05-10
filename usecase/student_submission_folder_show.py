from domain.model.value import StudentID
from infra.io.student_folder_show_in_explorer import StudentFolderShowInExplorerIO


class StudentSubmissionFolderShowUseCase:
    def __init__(
            self,
            *,
            student_folder_show_in_explorer_io: StudentFolderShowInExplorerIO,
    ):
        self._student_folder_show_in_explorer_io = student_folder_show_in_explorer_io

    def execute(self, student_id: StudentID) -> None:
        self._student_folder_show_in_explorer_io.show_submission_folder(student_id)
