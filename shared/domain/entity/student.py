from datetime import datetime

from shared.domain.value.identifier import StudentID


class StudentEntity:
    def __init__(
            self,
            *,
            student_id: StudentID,
            name: str,
            name_en: str,
            email_address: str,
            submitted_at: datetime | None,
            num_submissions: int,
            submission_folder_name: str | None,
    ):
        self._student_id = student_id  # IDフィールド: immutable
        self.name = name
        self.name_en = name_en
        self.email_address = email_address
        self.submitted_at = submitted_at
        self.num_submissions = num_submissions
        self.submission_folder_name = submission_folder_name

        self._validate()

    def _validate(self):
        if not isinstance(self._student_id, StudentID):
            raise TypeError(
                f"Expected 'student_id' to be StudentID, "
                f"got {type(self._student_id).__name__}: {self._student_id!r}"
            )
        if not isinstance(self.name, str):
            raise TypeError(
                f"Expected 'name' to be str, "
                f"got {type(self.name).__name__}: {self.name!r}"
            )
        if not isinstance(self.name_en, str):
            raise TypeError(
                f"Expected 'name_en' to be str, "
                f"got {type(self.name_en).__name__}: {self.name_en!r}"
            )
        if not isinstance(self.email_address, str):
            raise TypeError(
                f"Expected 'email_address' to be str, "
                f"got {type(self.email_address).__name__}: {self.email_address!r}"
            )
        if self.submitted_at is not None and not isinstance(self.submitted_at, datetime):
            raise TypeError(
                f"Expected 'submitted_at' to be datetime or None, "
                f"got {type(self.submitted_at).__name__}: {self.submitted_at!r}"
            )
        if not isinstance(self.num_submissions, int):
            raise TypeError(
                f"Expected 'num_submissions' to be int, "
                f"got {type(self.num_submissions).__name__}: {self.num_submissions!r}"
            )
        if self.submission_folder_name is not None and not isinstance(self.submission_folder_name,
                                                                      str):
            raise TypeError(
                f"Expected 'submission_folder_name' to be str or None, "
                f"got {type(self.submission_folder_name).__name__}: {self.submission_folder_name!r}"
            )

    @property
    def student_id(self) -> StudentID:
        """IDフィールド: Getterのみ（変更不可）"""
        return self._student_id

    def __eq__(self, other):
        """IDベースの等価性判定"""
        if not isinstance(other, StudentEntity):
            return False
        return self._student_id == other._student_id

    def __hash__(self):
        """IDベースのハッシュ"""
        return hash(self._student_id)

    def to_json(self):
        return dict(
            student_id=self._student_id.to_json(),
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
