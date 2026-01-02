from shared.domain.value.identifier import StudentID


class StudentMarkEntity:
    def __init__(self, student_id: StudentID, score: int | None):  # Noneは未採点を表す
        self._student_id = student_id  # IDフィールド: immutable
        self._score = score  # mutable

        self._validate()

    def _validate(self):
        if not isinstance(self._student_id, StudentID):
            raise TypeError(
                f"Expected 'student_id' to be StudentID, "
                f"got {type(self._student_id).__name__}: {self._student_id!r}"
            )
        if self._score is not None and not isinstance(self._score, int):
            raise TypeError(
                f"Expected 'score' to be int or None, "
                f"got {type(self._score).__name__}: {self._score!r}"
            )

    @property
    def student_id(self) -> StudentID:
        """IDフィールド: Getterのみ（変更不可）"""
        return self._student_id

    def __eq__(self, other):
        """IDベースの等価性判定"""
        if not isinstance(other, StudentMarkEntity):
            return False
        return self._student_id == other._student_id

    def __hash__(self):
        """IDベースのハッシュ"""
        return hash(self._student_id)

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
            raise ValueError("This StudentEntity has not been marked yet")
        return self._score

    @score.setter
    def score(self, score: int) -> None:
        assert score is not None
        self._score = score

    def __repr__(self):
        return f"StudentMarkEntity(student_id={self._student_id}, score={self._score})"
