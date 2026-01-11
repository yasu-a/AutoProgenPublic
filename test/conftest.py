import json
import pytest
from shared.domain.entity.student import StudentEntity
from pathlib import Path


class Static:
    def __init__(
        self,
        student_path: Path,
    ):
        self._student_path = student_path

    @property
    def students(self) -> list[StudentEntity]:
        with self._student_path.open(encoding="utf-8") as f:
            students = json.load(f)
        return [StudentEntity.from_json(student) for student in students]


@pytest.fixture()
def student_path() -> Path:
    return Path("static/test/master.json")


@pytest.fixture()
def static(student_path: Path) -> Static:
    return Static(
        student_path=student_path,
    )
