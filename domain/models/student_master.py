from dataclasses import dataclass
from datetime import datetime

from domain.models.values import StudentID


@dataclass(slots=True)
class Student:
    student_id: StudentID
    name: str
    name_en: str
    email_address: str
    submitted_at: datetime | None
    num_submissions: int
    submission_folder_name: str | None

    def to_json(self):
        return dict(
            student_id=self.student_id.to_json(),
            name=self.name,
            name_en=self.name_en,
            email_address=self.email_address,
            submitted_at=(
                None
                if self.submitted_at is None
                else self.submitted_at.timestamp()
            ),
            num_submissions=self.num_submissions,
            submission_folder_name=self.submission_folder_name,
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            student_id=StudentID.from_json(body["student_id"]),
            name=body["name"],
            name_en=body["name_en"],
            email_address=body["email_address"],
            submitted_at=(
                None
                if body["submitted_at"] is None
                else datetime.fromtimestamp(body["submitted_at"])
            ),
            num_submissions=body["num_submissions"],
            submission_folder_name=body["submission_folder_name"],
        )

    @property
    def is_submitted(self) -> bool:
        return self.submission_folder_name is not None


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
