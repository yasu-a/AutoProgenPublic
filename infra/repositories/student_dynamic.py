from domain.models.file_item import SourceFileItem, ExecutableFileItem
from domain.models.values import StudentID
from infra.io.project_database import ProjectDatabaseIO


class StudentExecutableRepository:
    def __init__(
            self,
            *,
            project_database_io: ProjectDatabaseIO,
    ):
        self._project_database_io = project_database_io

    def _create_database_if_not_exists(self):
        with self._project_database_io.connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS student_executable
                (
                    student_id    TEXT PRIMARY KEY,
                    content_bytes BLOB
                )
                """
            )
            # TODO: create student master table and make student_id as a foreign key
            con.commit()

    def put(self, student_id: StudentID, file_item: ExecutableFileItem) -> None:
        self._create_database_if_not_exists()
        with self._project_database_io.connect() as con:
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
        self._create_database_if_not_exists()
        with self._project_database_io.connect() as con:
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
        self._create_database_if_not_exists()
        with self._project_database_io.connect() as con:
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
        self._create_database_if_not_exists()
        with self._project_database_io.connect() as con:
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


class StudentSourceRepository:
    def __init__(
            self,
            *,
            project_database_io: ProjectDatabaseIO,
    ):
        self._project_database_io = project_database_io

    def _create_database_if_not_exists(self):
        with self._project_database_io.connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS student_source
                (
                    student_id    TEXT PRIMARY KEY,
                    content_bytes BLOB,
                    encoding      TEXT
                )
                """
            )
            # TODO: create student master table and make student_id as a foreign key
            con.commit()

    def put(self, student_id: StudentID, file_item: SourceFileItem) -> None:
        self._create_database_if_not_exists()
        with self._project_database_io.connect() as con:
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
        self._create_database_if_not_exists()
        with self._project_database_io.connect() as con:
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
        self._create_database_if_not_exists()
        with self._project_database_io.connect() as con:
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
        self._create_database_if_not_exists()
        with self._project_database_io.connect() as con:
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
