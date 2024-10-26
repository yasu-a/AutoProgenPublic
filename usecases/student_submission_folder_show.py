from domain.models.values import StudentID
from services.student_submission import StudentSubmissionFolderShowService


class StudentSubmissionFolderShowUseCase:
    def __init__(
            self,
            *,
            student_submission_folder_show_service: StudentSubmissionFolderShowService,
    ):
        self._student_submission_folder_show_service = student_submission_folder_show_service

    def execute(self, student_id: StudentID) -> None:
        self._student_submission_folder_show_service.execute(student_id)
