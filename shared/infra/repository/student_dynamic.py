from pathlib import Path

from shared.domain.interface.repository import IStudentExecutableRepository, \
    IStudentSourceRepository
from shared.domain.value.file_item import SourceFileItem, ExecutableFileItem
from shared.domain.value.identifier import StudentID
from shared.infra.system.database import DatabaseManager


class StudentExecutableRepository(IStudentExecutableRepository):
    def __init__(
            self,
            *,
            db_path: Path,
    ):
        self._db = DatabaseManager(db_path=db_path)

    def put(self, student_id: StudentID, file_item: ExecutableFileItem) -> None:
        with self._db.connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                INSERT OR REPLACE INTO student_executable
                (
                    student_id,
                    content_bytes
                )
                VALUES (?, ?)
                """,
                (str(student_id), file_item.content_bytes),
            )
            con.commit()

    def get(self, student_id: StudentID) -> ExecutableFileItem:
        with self._db.connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                SELECT content_bytes
                FROM student_executable
                WHERE student_id = ?
                """,
                (str(student_id),),
            )
            row = cur.fetchone()
        if row is None:
            raise FileNotFoundError()
        return ExecutableFileItem(
            content_bytes=row["content_bytes"],
        )

    def exists(self, student_id: StudentID) -> bool:
        with self._db.connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                SELECT EXISTS (SELECT 1
                               FROM student_executable
                               WHERE student_id = ?)
                """,
                (str(student_id),),
            )
            return bool(cur.fetchone()[0])

    def delete(self, student_id: StudentID) -> None:
        with self._db.connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                DELETE
                FROM student_executable
                WHERE student_id = ?
                """,
                (str(student_id),),
            )
            if cur.rowcount == 0:
                raise FileNotFoundError()
            con.commit()


class StudentSourceRepository(IStudentSourceRepository):
    def __init__(self, db_path: Path):
        self._db = DatabaseManager(db_path)

    def put(self, student_id: StudentID, file_item: SourceFileItem) -> None:
        with self._db.connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                INSERT OR REPLACE INTO student_source
                (
                    student_id,
                    content_bytes,
                    encoding
                )
                VALUES (?, ?, ?)
                """,
                (str(student_id), file_item.content_bytes, file_item.encoding),
            )
            con.commit()

    def get(self, student_id: StudentID) -> SourceFileItem:
        with self._db.connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                SELECT content_bytes, encoding
                FROM student_source
                WHERE student_id = ?
                """,
                (str(student_id),),
            )
            row = cur.fetchone()
        if row is None:
            raise FileNotFoundError()
        return SourceFileItem(
            content_bytes=row["content_bytes"],
            encoding=row["encoding"],
        )

    def exists(self, student_id: StudentID) -> bool:
        with self._db.connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                SELECT EXISTS (SELECT 1
                               FROM student_source
                               WHERE student_id = ?)
                """,
                (str(student_id),),
            )
            return bool(cur.fetchone()[0])

    def delete(self, student_id: StudentID) -> None:
        with self._db.connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                DELETE
                FROM student_source
                WHERE student_id = ?
                """,
                (str(student_id),),
            )
            if cur.rowcount == 0:
                raise FileNotFoundError()
            con.commit()
