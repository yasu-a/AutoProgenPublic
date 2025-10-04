from domain.model.student import Student
from domain.model.value import StudentID
from service.student import StudentListSubService


class StudentListIDUseCase:
    def __init__(
            self,
            *,
            student_list_sub_service: StudentListSubService,
    ):
        self._student_list_sub_service = student_list_sub_service

    def execute(self) -> list[StudentID]:
        students: list[Student] = self._student_list_sub_service.execute()
        return [student.student_id for student in students]
