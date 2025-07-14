from contextlib import contextmanager
from datetime import datetime

from PyQt5.QtCore import QMutex

from domain.errors import RepositoryItemNotFoundError
from domain.models.student_mark import StudentMark
from domain.models.values import StudentID
from infra.io.project_database import ProjectDatabaseIO


class StudentMarkRepository:
    def __init__(
            self,
            *,
            project_database_io: ProjectDatabaseIO,
    ):
        self._project_database_io = project_database_io
        self._lock = QMutex()

    @contextmanager
    def __lock(self):
        self._lock.lock()
        try:
            yield
        finally:
            self._lock.unlock()

    def _create_database_if_not_exists(self):
        with self._project_database_io.connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS student_mark
                (
                    student_id TEXT NOT NULL PRIMARY KEY,
                    score      INTEGER,
                    updated_at DATETIME,
                    FOREIGN KEY (student_id) REFERENCES student (student_id)
                )
                """
            )
            con.commit()

    def create(self, student_id: StudentID) -> StudentMark:
        mark = StudentMark(
            student_id=student_id,
            score=None,
        )
        self.put(mark=mark)
        return mark

    def put(self, mark: StudentMark) -> StudentMark:
        with self.__lock():
            self._create_database_if_not_exists()
            with self._project_database_io.connect() as con:
                cur = con.cursor()
                cur.execute(
                    """
                    INSERT OR REPLACE INTO student_mark
                    (
                        student_id,
                        score,
                        updated_at
                    )
                    VALUES (?, ?, ?)
                    """,
                    (str(mark.student_id), mark.score if mark.is_marked else None, datetime.now()),
                )
                con.commit()
        return mark

    def exists(self, student_id: StudentID) -> bool:
        with self.__lock():
            self._create_database_if_not_exists()
            with self._project_database_io.connect() as con:
                cur = con.cursor()
                cur.execute(
                    """
                    SELECT EXISTS (SELECT 1
                                   FROM student_mark
                                   WHERE student_id = ?)
                    """,
                    (str(student_id),),
                )
                return bool(cur.fetchone()[0])

    def get(self, student_id: StudentID) -> StudentMark:
        with self.__lock():
            self._create_database_if_not_exists()
            with self._project_database_io.connect() as con:
                cur = con.cursor()
                cur.execute(
                    """
                    SELECT *
                    FROM student_mark
                    WHERE student_id = ?
                    """,
                    (str(student_id),),
                )
                row = cur.fetchone()
            if row is None:
                raise RepositoryItemNotFoundError(f"Mark data for student {student_id} not found")
            return StudentMark(
                student_id=StudentID(row["student_id"]),
                score=row["score"],
            )

    def get_timestamp(self, student_id: StudentID) -> datetime | None:
        with self.__lock():
            self._create_database_if_not_exists()
            with self._project_database_io.connect() as con:
                cur = con.cursor()
                cur.execute(
                    """
                    SELECT updated_at
                    FROM student_mark
                    WHERE student_id = ?
                    """,
                    (str(student_id),),
                )
                row = cur.fetchone()
            if row is None:
                return None
            return row["updated_at"]

    def list(self) -> list[StudentMark]:
        with self.__lock():
            self._create_database_if_not_exists()
            with self._project_database_io.connect() as con:
                cur = con.cursor()
                cur.execute(
                    """
                    SELECT *
                    FROM student_mark
                    ORDER BY student_id
                    """
                )
                marks = []
                for row in cur:
                    marks.append(
                        StudentMark(
                            student_id=StudentID(row["student_id"]),
                            score=row["score"],
                        )
                    )
                return marks
