from domain.models.file_item import SourceFileItem
from domain.models.values import StudentID
from infra.repositories.student_dynamic import StudentDynamicRepository


class StudentSourceCodeGetQueryService:
    def __init__(
            self,
            *,
            student_dynamic_repo: StudentDynamicRepository,
    ):
        self._student_dynamic_repo = student_dynamic_repo

    def execute(self, student_id: StudentID) -> str:
        if not self._student_dynamic_repo.exists(
                student_id=student_id,
                file_item_type=SourceFileItem,
        ):
            raise FileNotFoundError()

        content_text = self._student_dynamic_repo.get(
            student_id=student_id,
            file_item_type=SourceFileItem,
        ).content_text

        # FIXME: content_textが一行おきに空行になる どこが原因？それとも元から1行おき？
        # content_text = content_text.replace("\r\n", "\n")  # 効果なし

        return content_text
