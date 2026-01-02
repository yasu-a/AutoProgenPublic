from contextlib import contextmanager

from PyQt5.QtCore import QMutex

from shared.domain.entity.student import StudentEntity
from shared.domain.error import RepositoryItemNotFoundError
from shared.domain.interface.repository import IStudentRepository
from shared.domain.value.identifier import StudentID
from shared.infra.system.project_database import ProjectDatabaseIO


class InMemoryStudentRepository(IStudentRepository):
    """メモリ上で動作するStudentRepositoryの実装"""
    
    def __init__(self, students: list[StudentEntity] | None = None):
        """
        初期化
        
        Args:
            students: 初期データとして設定する生徒のリスト（省略可）
        """
        self._students: dict[StudentID, StudentEntity] = {}
        if students is not None:
            for student in students:
                self._students[student.student_id] = student
    
    def create_all(self, students: list[StudentEntity]) -> None:
        """すべての生徒をメモリに保存"""
        for student in students:
            self._students[student.student_id] = student
    
    def exists_any(self) -> bool:
        """生徒データが存在するか"""
        return len(self._students) > 0
    
    def get(self, student_id: StudentID) -> StudentEntity:
        """生徒を取得"""
        if student_id not in self._students:
            raise RepositoryItemNotFoundError(f"StudentEntity {student_id} not found")
        return self._students[student_id]
    
    def list(self) -> list[StudentEntity]:
        """すべての生徒を取得"""
        return list(self._students.values())


class StudentRepository:
    # 生徒マスタから生徒のメタデータ（Studentインスタンス）を読み書きするレポジトリ

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
                CREATE TABLE IF NOT EXISTS StudentEntity
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

    def create_all(self, students: list[StudentEntity]) -> None:
        with self.__lock():
            self._create_database_if_not_exists()
            with self._project_database_io.connect() as con:
                cur = con.cursor()
                cur.executemany(
                    """
                    INSERT INTO StudentEntity (student_id,
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
                                   FROM StudentEntity)
                    """
                )
                return bool(cur.fetchone()[0])

    def get(self, student_id: StudentID) -> StudentEntity:
        with self.__lock():
            self._create_database_if_not_exists()
            with self._project_database_io.connect() as con:
                cur = con.cursor()
                cur.execute(
                    """
                    SELECT *
                    FROM StudentEntity
                    WHERE student_id = ?
                    """,
                    (str(student_id),),
                )
                row = cur.fetchone()
            if row is None:
                raise RepositoryItemNotFoundError(f"StudentEntity {student_id} not found")
            return StudentEntity(
                student_id=StudentID(row["student_id"]),
                name=row["name"],
                name_en=row["name_en"],
                email_address=row["email_address"],
                submitted_at=row["submitted_at"],
                num_submissions=row["num_submissions"],
                submission_folder_name=row["submission_folder_name"],
            )

    def list(self) -> list[StudentEntity]:
        with self.__lock():
            self._create_database_if_not_exists()
            with self._project_database_io.connect() as con:
                cur = con.cursor()
                cur.execute(
                    """
                    SELECT *
                    FROM StudentEntity
                    ORDER BY student_id
                    """
                )
                students = []
                for row in cur:
                    students.append(
                        StudentEntity(
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

# class StudentRepository:
#     def __init__(
#             self,
#             *,
#             student_repo_no_cache: StudentRepositoryNoCache,
#     ):
#         self._student_repo_no_cache = student_repo_no_cache
#
#         self._student_cache: dict[StudentID, StudentEntity] | None = None
#         self._lock = QMutex()
#
#     def _invalidate_cache_unlocked(self):
#         self._student_cache = None
#
#     def _get_student_cache_unlocked(self) -> dict[StudentID, StudentEntity]:
#         if self._student_cache is None:
#             self._student_cache = {}
#             for StudentEntity in self._student_repo_no_cache.list():
#                 self._student_cache[StudentEntity.student_id] = copy.deepcopy(StudentEntity)
#         return self._student_cache
#
#     @contextmanager
#     def __lock(self):
#         self._lock.lock()
#         try:
#             yield
#         finally:
#             self._lock.unlock()
#
#     def create_all(self, students: list[StudentEntity]) -> None:
#         with self.__lock():
#             self._student_repo_no_cache.create_all(students)
#             self._invalidate_cache_unlocked()
#
#     def exists_any(self) -> bool:
#         # 何らかの生徒データが存在する場合にTrueを返す
#         with self.__lock():
#             cache = self._get_student_cache_unlocked()
#             return bool(cache)
#
#     def get(self, student_id: StudentID) -> StudentEntity:
#         with self.__lock():
#             cache = self._get_student_cache_unlocked()
#             if student_id not in cache:
#                 raise RepositoryItemNotFoundError(f"StudentEntity {student_id} not found")
#             return copy.deepcopy(cache[student_id])
#
#     def list(self) -> list[StudentEntity]:
#         with self.__lock():
#             cache = self._get_student_cache_unlocked()
#             return copy.deepcopy(list(cache.values()))
