from autoprogen.domain.model.source_code import SourceCode
from autoprogen.domain.model.value import StudentID
from autoprogen.infra.io.project_database import ProjectDatabaseIO


class StudentSourceRepository:
    """学生の正規化済みソースコードをプロジェクトDBへ保存する。"""

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
                    encoding TEXT,
                    FOREIGN KEY (student_id) REFERENCES student (student_id)
                )
                """
            )
            con.commit()

    def put(self, student_id: StudentID, source_code: SourceCode) -> None:
        """ソースコードを既存形式のUTF-8 BLOBとして保存する。"""
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
                (str(student_id), source_code.to_utf8_bytes(), "utf-8"),
            )
            con.commit()

    def get(self, student_id: StudentID) -> SourceCode:
        """既存DBの文字コード情報を使ってソースコードを復元する。"""
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
        source_code_text = row["content_bytes"].decode(row["encoding"])
        return SourceCode(text=source_code_text)

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
