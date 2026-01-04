from shared.domain.interface.service import IStudentDynamicClearService, \
    IStudentDynamicSetSourceContentService
from shared.domain.value.file_item import SourceFileItem
from shared.domain.value.identifier import StudentID
from shared.infra.repository.student_dynamic import StudentSourceRepository, \
    StudentExecutableRepository


class StudentDynamicClearService(IStudentDynamicClearService):
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


class StudentDynamicSetSourceContentService(IStudentDynamicSetSourceContentService):
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
