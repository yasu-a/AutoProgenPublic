from contextlib import contextmanager
from datetime import datetime

from PyQt5.QtCore import QMutex

from shared.domain.entity.student_mark import StudentMarkEntity
from shared.domain.error import RepositoryItemNotFoundError
from shared.domain.interface.repository import IStudentScoreRepository
from shared.domain.value.identifier import StudentID
from shared.infra.system.project_database import ProjectDatabaseIO


class InMemoryStudentScoreRepository(IStudentScoreRepository):
    """メモリ上で動作するStudentScoreRepositoryの実装"""
    
    def __init__(self, marks: list[StudentMarkEntity] | None = None):
        """
        初期化
        
        Args:
            marks: 初期データとして設定する点数データのリスト（省略可）
        """
        self._marks: dict[StudentID, StudentMarkEntity] = {}
        if marks is not None:
            for mark in marks:
                self._marks[mark.student_id] = mark
    
    def create(self, student_id: StudentID) -> StudentMarkEntity:
        """未採点の点数データを作成"""
        mark = StudentMarkEntity(
            student_id=student_id,
            score=None,
        )
        self.put(mark)
        return mark
    
    def put(self, mark: StudentMarkEntity) -> StudentMarkEntity:
        """点数データをメモリに保存"""
        self._marks[mark.student_id] = mark
        return mark
    
    def exists(self, student_id: StudentID) -> bool:
        """点数データが存在するか"""
        return student_id in self._marks
    
    def get(self, student_id: StudentID) -> StudentMarkEntity:
        """点数データを取得"""
        if student_id not in self._marks:
            raise RepositoryItemNotFoundError(
                f"Mark data for StudentEntity {student_id} not found")
        return self._marks[student_id]
    
    def list(self) -> list[StudentMarkEntity]:
        """すべての点数データを取得"""
        return list(self._marks.values())


class StudentMarkEntityRepository(IStudentScoreRepository):
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

    def create(self, student_id: StudentID) -> StudentMarkEntity:
        mark = StudentMarkEntity(
            student_id=student_id,
            score=None,
        )
        self.put(mark=mark)
        return mark

    def put(self, mark: StudentMarkEntity) -> StudentMarkEntity:
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

    def get(self, student_id: StudentID) -> StudentMarkEntity:
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
                raise RepositoryItemNotFoundError(
                    f"Mark data for StudentEntity {student_id} not found")
            return StudentMarkEntity(
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

    def list(self) -> list[StudentMarkEntity]:
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
                        StudentMarkEntity(
                            student_id=StudentID(row["student_id"]),
                            score=row["score"],
                        )
                    )
                return marks
