from app_logging import create_logger
from domain.models.student_master import Student
from domain.models.values import TargetID, ProjectID, StudentID
from files.project import ProjectIO
from files.repositories.current_project import CurrentProjectRepository
from files.repositories.student import StudentRepository
from files.testcase import TestCaseIO


class ProjectService:  # TODO: ProgressServiceを分離する
    _logger = create_logger()

    def __init__(
            self,
            *,
            project_io: ProjectIO,
            current_project_repo: CurrentProjectRepository,
            testcase_io: TestCaseIO,
            student_repo: StudentRepository,
    ):
        self._project_io = project_io
        self._current_project_repo = current_project_repo
        self._testcase_io = testcase_io
        self._student_repo = student_repo

    def get_project_id(self) -> ProjectID:
        return self._current_project_repo.get().project_id

    def get_target_id(self) -> TargetID:
        return self._current_project_repo.get().target_id

    def get_student_ids(self) -> list[StudentID]:
        return [student.student_id for student in self._student_repo.list()]

    def has_student_submission_folder(self, student_id: StudentID) -> bool:
        return self._project_io.has_student_submission_folder(student_id)

    def show_student_submission_folder_in_explorer(self, student_id: StudentID) -> None:
        self._project_io.show_student_submission_folder_in_explorer(student_id)

    def get_student(self, student_id: StudentID) -> Student:
        return self._student_repo.get(student_id)
