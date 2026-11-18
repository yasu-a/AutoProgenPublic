from autoprogen.domain.model.value import StudentID


class StudentMark:
    """学生の学籍番号と点数を管理する。"""

    def __init__(
        self,
        student_id: StudentID,
        score: int | None,
    ) -> None:
        """学生の学籍番号と点数を保持する。"""
        self._student_id = student_id
        self._score = score

    @property
    def student_id(self) -> StudentID:
        """学生IDを返す。"""
        return self._student_id

    @property
    def marked(self) -> bool:
        """点数が入力されているかを返す。"""
        return self._score is not None

    @property
    def score(self) -> int | None:
        """点数を返す。未採点の場合はNoneを返す。"""
        return self._score

    @score.setter
    def score(self, score: int | None) -> None:
        """点数を更新する。"""
        self._score = score

    def __repr__(self) -> str:
        """デバッグ用の文字列表現を返す。"""
        return f"StudentMark(student_id={self._student_id}, score={self._score})"
