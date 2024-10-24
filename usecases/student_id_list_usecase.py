from domain.models.student_master import StudentMaster
from domain.models.values import StudentID
from services.student_list import StudentListService


class StudentIDListUseCase:
    def __init__(
            self,
            *,
            student_list_service: StudentListService,
    ):
        self._student_list_service = student_list_service

    def execute(self) -> list[StudentID]:
        students: StudentMaster = self._student_list_service.execute()
        return [student.student_id for student in students]
