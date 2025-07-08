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
    submission_folder_name: str | None  # None if the student has no submission

    def __post_init__(self):
        assert isinstance(self.student_id, StudentID), \
            (self.student_id, type(self.student_id))
        assert isinstance(self.name, str), \
            (self.name, type(self.name))
        assert isinstance(self.name_en, str), \
            (self.name_en, type(self.name_en))
        assert isinstance(self.email_address, str), \
            (self.email_address, type(self.email_address))
        assert self.submitted_at is None or isinstance(self.submitted_at, datetime), \
            (self.submitted_at, type(self.submitted_at))
        assert isinstance(self.num_submissions, int), \
            (self.num_submissions, type(self.num_submissions))
        assert self.submission_folder_name is None or isinstance(self.submission_folder_name, str), \
            (self.submission_folder_name, type(self.submission_folder_name))

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
