from domain.models.student_master import StudentMaster
from domain.models.values import StudentID
from services.student import StudentListSubService


class StudentListIDUseCase:
    def __init__(
            self,
            *,
            student_list_sub_service: StudentListSubService,
    ):
        self._student_list_sub_service = student_list_sub_service

    def execute(self) -> list[StudentID]:
        students: StudentMaster = self._student_list_sub_service.execute()
        return [student.student_id for student in students]
