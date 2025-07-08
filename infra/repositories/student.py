from contextlib import contextmanager

from PyQt5.QtCore import QMutex

from domain.models.student import Student
from domain.models.values import StudentID
from infra.io.project_database import ProjectDatabaseIO


class StudentRepository:
    # 生徒マスタから生徒のメタデータ（Studentインスタンス）を読み書きするレポジトリ
    # FIXME: アクセスが遅い キャッシュを作る

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
                CREATE TABLE IF NOT EXISTS student
                (
                    student_id             TEXT    NOT NULL PRIMARY KEY,
                    name                   TEXT    NOT NULL,
                    name_en                TEXT    NOT NULL,
                    email_address          TEXT    NOT NULL,
                    submitted_at           DATETIME,
                    num_submissions        INTEGER NOT NULL,
                    submission_folder_name TEXT
                )
                """
            )
            con.commit()

    def create_all(self, students: list[Student]) -> None:
        with self.__lock():
            self._create_database_if_not_exists()
            with self._project_database_io.connect() as con:
                cur = con.cursor()
                cur.executemany(
                    """
                    INSERT INTO student (student_id,
                                         name,
                                         name_en,
                                         email_address,
                                         submitted_at,
                                         num_submissions,
                                         submission_folder_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            str(student.student_id),
                            student.name,
                            student.name_en,
                            student.email_address,
                            student.submitted_at,
                            student.num_submissions,
                            student.submission_folder_name,
                        ) for student in students
                    ]
                )
                con.commit()

    def exists_any(self) -> bool:
        # 何らかの生徒データが存在する場合にTrueを返す
        with self.__lock():
            self._create_database_if_not_exists()
            with self._project_database_io.connect() as con:
                cur = con.cursor()
                cur.execute(
                    """
                    SELECT EXISTS (SELECT 1
                                   FROM student)
                    """
                )
                return bool(cur.fetchone()[0])

    def get(self, student_id: StudentID) -> Student:
        with self.__lock():
            self._create_database_if_not_exists()
            with self._project_database_io.connect() as con:
                cur = con.cursor()
                cur.execute(
                    """
                    SELECT *
                    FROM student
                    WHERE student_id = ?
                    """,
                    (str(student_id),),
                )
                row = cur.fetchone()
            if row is None:
                raise ValueError(f"Student {student_id} not found")
            return Student(
                student_id=StudentID(row["student_id"]),
                name=row["name"],
                name_en=row["name_en"],
                email_address=row["email_address"],
                submitted_at=row["submitted_at"],
                num_submissions=row["num_submissions"],
                submission_folder_name=row["submission_folder_name"],
            )

    def list(self) -> list[Student]:
        with self.__lock():
            self._create_database_if_not_exists()
            with self._project_database_io.connect() as con:
                cur = con.cursor()
                cur.execute(
                    """
                    SELECT *
                    FROM student
                    ORDER BY student_id
                    """
                )
                students = []
                for row in cur:
                    students.append(
                        Student(
                            student_id=StudentID(row["student_id"]),
                            name=row["name"],
                            name_en=row["name_en"],
                            email_address=row["email_address"],
                            submitted_at=row["submitted_at"],
                            num_submissions=row["num_submissions"],
                            submission_folder_name=row["submission_folder_name"],
                        )
                    )
                return students
