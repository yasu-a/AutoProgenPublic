from domain.model.value import StudentID


class StudentMark:
    def __init__(self, student_id: StudentID, score: int | None):  # Noneは未採点を表す
        self._student_id = student_id
        self._score = score

    @property
    def student_id(self) -> StudentID:
        return self._student_id

    def to_json(self):
        return dict(
            student_id=self._student_id.to_json(),
            score=self._score,
        )

    @classmethod
    def from_json(cls, body):
        return cls(
            student_id=StudentID.from_json(body["student_id"]),
            score=body["score"],
        )

    @property
    def is_marked(self) -> bool:
        return self._score is not None

    def set_unmarked(self) -> None:
        self._score = None

    @property
    def score(self) -> int:
        if self._score is None:
            raise ValueError("This student has not been marked yet")
        return self._score

    @score.setter
    def score(self, score: int) -> None:
        assert score is not None
        self._score = score

    def __repr__(self):
        return f"StudentMark(student_id={self._student_id}, score={self._score})"
