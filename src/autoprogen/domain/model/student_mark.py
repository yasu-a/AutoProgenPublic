from autoprogen.domain.model.value import StudentID


class StudentMark:
    """学生の点数と採点の確定状態を管理する。"""

    def __init__(
        self,
        student_id: StudentID,
        score: int | None,
        confirmed: bool | None = None,
    ) -> None:
        """点数と、採点済みの場合は明示された確定状態を保持する。"""
        if score is None:
            if confirmed:
                raise ValueError("Cannot confirm an unmarked student")
            confirmed = False
        elif confirmed is None:
            raise ValueError("confirmed is required when score is set")

        self._student_id = student_id
        self._score = score
        self._confirmed = confirmed

    @property
    def student_id(self) -> StudentID:
        """学生IDを返す。"""
        return self._student_id

    @property
    def marked(self) -> bool:
        """点数が入力されているかを返す。"""
        return self._score is not None

    @property
    def confirmed(self) -> bool:
        """採点の確定状態を返す。"""
        return self._confirmed

    @confirmed.setter
    def confirmed(self, confirmed: bool) -> None:
        """未採点の確定を禁止し、確定状態を更新する。"""
        if confirmed and not self.marked:
            raise ValueError("Cannot confirm an unmarked student")
        self._confirmed = confirmed

    @property
    def score(self) -> int | None:
        """点数を返す。未採点の場合はNoneを返す。"""
        return self._score

    @score.setter
    def score(self, score: int | None) -> None:
        """点数を更新し、未採点になった場合だけ確定を解除する。"""
        self._score = score
        if score is None:
            self._confirmed = False

    def __repr__(self) -> str:
        """デバッグ用の文字列表現を返す。"""
        return (
            f"StudentMark(student_id={self._student_id}, "
            f"score={self._score}, confirmed={self._confirmed})"
        )
