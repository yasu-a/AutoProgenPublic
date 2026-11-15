from autoprogen.domain.model.source_code import SourceCode
from autoprogen.domain.model.value import StudentID
from autoprogen.infra.repository.student_executable import StudentExecutableRepository
from autoprogen.infra.repository.student_source_code import StudentSourceRepository


class StudentDynamicClearService:
    # 動的データをクリアする

    def __init__(
            self,
            *,
            student_source_repo: StudentSourceRepository,
            student_execute_repo: StudentExecutableRepository,
    ):
        self._student_source_repo = student_source_repo
        self._student_execute_repo = student_execute_repo

    def execute(self, *, student_id: StudentID) -> None:
        if self._student_source_repo.exists(student_id):
            self._student_source_repo.delete(student_id)

        if self._student_execute_repo.exists(student_id):
            self._student_execute_repo.delete(student_id)


class StudentDynamicSetSourceCodeService:
    """正規化済みソースコードを学生の動的データへ保存する。"""

    def __init__(
            self,
            *,
            student_source_repo: StudentSourceRepository,
    ):
        self._student_source_repo = student_source_repo

    def execute(self, *, student_id: StudentID, source_code: SourceCode) -> None:
        """指定した学生のソースコードを保存する。"""
        self._student_source_repo.put(
            student_id=student_id,
            source_code=source_code,
        )


class StudentDynamicGetSourceCodeService:
    """学生の動的データから正規化済みソースコードを取得する。"""

    def __init__(
            self,
            *,
            student_source_repo: StudentSourceRepository,
    ):
        self._student_source_repo = student_source_repo

    def execute(self, student_id: StudentID) -> SourceCode:
        """指定した学生のソースコードを返す。"""
        if not self._student_source_repo.exists(student_id):
            raise FileNotFoundError()

        source_code = self._student_source_repo.get(
            student_id=student_id,
        )

        return source_code
