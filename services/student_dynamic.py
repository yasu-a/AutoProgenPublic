from domain.models.file_item import SourceFileItem
from domain.models.values import StudentID
from infra.repositories.student_dynamic import StudentSourceRepository, \
    StudentExecutableRepository


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


class StudentDynamicSetSourceContentService:
    def __init__(
            self,
            *,
            student_source_repo: StudentSourceRepository,
    ):
        self._student_source_repo = student_source_repo

    def execute(self, *, student_id: StudentID, source_content_text: str) -> None:
        self._student_source_repo.put(
            student_id=student_id,
            file_item=SourceFileItem(
                content_bytes=source_content_text.encode("utf-8"),
                encoding="utf-8",
            )
        )


class StudentDynamicGetSourceContentService:
    def __init__(
            self,
            *,
            student_source_repo: StudentSourceRepository,
    ):
        self._student_source_repo = student_source_repo

    def execute(self, student_id: StudentID) -> str:
        if not self._student_source_repo.exists(student_id):
            raise FileNotFoundError()

        content_text = self._student_source_repo.get(
            student_id=student_id,
        ).content_text

        return content_text
