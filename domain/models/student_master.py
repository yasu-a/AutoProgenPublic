from domain.models.student import Student
from domain.models.values import StudentID


class StudentMaster(list[Student]):
    def __getitem__(self, student_id: StudentID) -> Student:
        for student in self:
            if student.student_id == student_id:
                return student
        raise ValueError("Student is not found", student_id)

    def to_json(self):
        return [
            student.to_json()
            for student in self
        ]

    @classmethod
    def from_json(cls, body):
        return cls(
            [
                Student.from_json(student)
                for student in body
            ]
        )

    def is_empty(self) -> bool:
        return len(self) == 0
