from datetime import datetime

from domain.model.value import StudentID
from infra.io.project_database import ProjectDatabaseIO


class _ResultTimestampHelper:
    """結果タイムスタンプ管理ヘルパー"""

    def __init__(self, *, project_database_io: ProjectDatabaseIO):
        self._project_database_io = project_database_io
        self._create_table_if_not_exists()
        self._cache = {}

    def _create_table_if_not_exists(self):
        """タイムスタンプテーブルが存在しない場合に作成"""
        with self._project_database_io.connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS student_stage_path_result_timestamp
                (
                    student_id TEXT PRIMARY KEY,
                    timestamp  DATETIME NOT NULL,
                    FOREIGN KEY (student_id) REFERENCES student (student_id)
                )
                """
            )
            con.commit()

    def update(self, student_id: StudentID, cursor) -> None:
        """
        指定された生徒IDの現在の時刻を記録（または更新）します。
        """
        timestamp = datetime.now()  # 現在時刻を取得
        self._cache[student_id] = timestamp

        cursor.execute(
            """
            INSERT OR REPLACE INTO student_stage_path_result_timestamp (student_id, timestamp)
            VALUES (?, ?)
            """,
            (str(student_id), timestamp),
        )

    def get(self, student_id: StudentID, cursor) -> datetime | None:
        """
        指定された生徒IDの記録された時刻を取得します。
        記録がない場合は None を返します。
        """
        if student_id not in self._cache:
            cursor.execute(
                """
                SELECT timestamp
                FROM student_stage_path_result_timestamp
                WHERE student_id = ?
                """,
                (str(student_id),),
            )
            row = cursor.fetchone()
            if row is None:
                timestamp = None
            else:
                timestamp = row["timestamp"]
            self._cache[student_id] = timestamp
        return self._cache[student_id]
