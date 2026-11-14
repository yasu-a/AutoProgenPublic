from pathlib import Path

from autoprogen.domain.model.source_code import SourceCode
from autoprogen.domain.model.value import StudentID
from autoprogen.infra.io.project_database import ProjectDatabaseIO
from autoprogen.infra.repository.student_source_code import StudentSourceRepository


def _create_repository(database_path: Path) -> tuple[
    StudentSourceRepository,
    ProjectDatabaseIO,
]:
    """外部キーの参照先を用意した学生ソースRepositoryを作成する。"""
    database_io = ProjectDatabaseIO(database_path=database_path)
    with database_io.connect() as connection:
        connection.execute(
            "CREATE TABLE student (student_id TEXT NOT NULL PRIMARY KEY)"
        )
        connection.execute(
            "INSERT INTO student (student_id) VALUES (?)",
            ("00A0000000A",),
        )
        connection.commit()
    return StudentSourceRepository(project_database_io=database_io), database_io


def test_student_source_repository_preserves_existing_storage_format(
    tmp_path: Path,
) -> None:
    """SourceCodeを従来どおりUTF-8 BLOBとencoding列へ保存することを確認する。"""
    repository, database_io = _create_repository(tmp_path / "project.sqlite3")
    student_id = StudentID("00A0000000A")
    source_code = SourceCode(text="// 日本語\nint main(void) { return 0; }\n")

    repository.put(student_id, source_code)

    with database_io.connect() as connection:
        row = connection.execute(
            "SELECT content_bytes, encoding FROM student_source WHERE student_id = ?",
            (str(student_id),),
        ).fetchone()
    assert row is not None
    assert row["content_bytes"] == source_code.to_utf8_bytes()
    assert row["encoding"] == "utf-8"
    assert repository.get(student_id) == source_code


def test_student_source_repository_reads_existing_encoded_row(tmp_path: Path) -> None:
    """既存DBのencoding列に従って保存済みBLOBを復元できることを確認する。"""
    repository, database_io = _create_repository(tmp_path / "legacy.sqlite3")
    student_id = StudentID("00A0000000A")
    source_code_text = "// 日本語\nint main(void) { return 0; }\n"

    assert not repository.exists(student_id)
    with database_io.connect() as connection:
        connection.execute(
            """
            INSERT INTO student_source (student_id, content_bytes, encoding)
            VALUES (?, ?, ?)
            """,
            (str(student_id), source_code_text.encode("shift-jis"), "shift-jis"),
        )
        connection.commit()

    assert repository.get(student_id) == SourceCode(text=source_code_text)
