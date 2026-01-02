from feature.workspace.usecase.interface import IStudentSubmissionFolderShowUseCase
from shared.domain.interface.gateway import IStudentSubmissionFolderShowGateway
from shared.domain.value.identifier import StudentID


class StudentSubmissionFolderShowUseCase(IStudentSubmissionFolderShowUseCase):
    def __init__(
            self,
            *,
            student_submission_folder_show_gateway: IStudentSubmissionFolderShowGateway,
    ):
        self._student_submission_folder_show_gateway = student_submission_folder_show_gateway

    def execute(self, student_id: StudentID) -> None:
        self._student_submission_folder_show_gateway.execute(student_id)
