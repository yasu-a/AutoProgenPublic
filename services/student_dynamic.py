from domain.models.file_item import SourceFileItem, ExecutableFileItem
from domain.models.values import StudentID
from infra.repositories.student_dynamic import StudentDynamicRepository


class StudentDynamicClearService:
    # 動的データをクリアする

    def __init__(
            self,
            *,
            student_dynamic_repo: StudentDynamicRepository,
    ):
        self._student_dynamic_repo = student_dynamic_repo

    def execute(self, *, student_id: StudentID) -> None:
        if self._student_dynamic_repo.exists(
                student_id=student_id,
                file_item_type=SourceFileItem,
        ):
            self._student_dynamic_repo.delete(
                student_id=student_id,
                file_item_type=SourceFileItem,
            )

        if self._student_dynamic_repo.exists(
                student_id=student_id,
                file_item_type=ExecutableFileItem,
        ):
            self._student_dynamic_repo.delete(
                student_id=student_id,
                file_item_type=ExecutableFileItem,
            )


class StudentDynamicSetSourceContentService:
    def __init__(
            self,
            *,
            student_dynamic_repo: StudentDynamicRepository,
    ):
        self._student_dynamic_repo = student_dynamic_repo

    def execute(self, *, student_id: StudentID, source_content_text: str) -> None:
        self._student_dynamic_repo.put(
            student_id=student_id,
            file_item=SourceFileItem(
                content_bytes=source_content_text.encode("utf-8"),
                encoding="utf-8",
            )
        )
