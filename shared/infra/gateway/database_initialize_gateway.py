from pathlib import Path

from shared.domain.interface.gateway import IDatabaseInitializeGateway
from shared.infra.system.database import DatabaseManager


class DatabaseInitializeGateway(IDatabaseInitializeGateway):
    """データベーススキーマ初期化Gateway"""

    def __init__(self, db_path: Path):
        self._db_io = DatabaseManager(db_path)

    def initialize(self) -> None:
        """データベースの全テーブルを作成する（冪等）"""
        with self._db_io.connect() as con:
            cur = con.cursor()

            # === 順序管理（外部キー制約を考慮） ===

            # 1. 親テーブル: student
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

            # 2. 親テーブル: testcase_config
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS testcase_config
                (
                    testcase_id TEXT NOT NULL PRIMARY KEY,
                    execute_config_json TEXT NOT NULL,
                    test_config_json TEXT NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
                """
            )

            # 3. student依存テーブル: student_executable
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS student_executable
                (
                    student_id    TEXT NOT NULL PRIMARY KEY,
                    content_bytes BLOB NOT NULL,
                    FOREIGN KEY (student_id) REFERENCES student (student_id)
                )
                """
            )

            # 4. student依存テーブル: student_source
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

            # 5. student依存テーブル: student_mark
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

            # 6. student依存テーブル: result_build
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS result_build (
                    student_id    TEXT NOT NULL PRIMARY KEY,
                    is_success    INTEGER NOT NULL,
                    timestamp     DATETIME NOT NULL,
                    error_summary TEXT,
                    submission_folder_checksum TEXT,
                    FOREIGN KEY (student_id) REFERENCES student (student_id)
                        ON DELETE CASCADE
                )
                """
            )

            # 7. student依存テーブル: result_compile
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS result_compile (
                    student_id    TEXT NOT NULL PRIMARY KEY,
                    is_success    INTEGER NOT NULL,
                    timestamp     DATETIME NOT NULL,
                    error_summary TEXT,
                    compiler_output TEXT,
                    FOREIGN KEY (student_id) REFERENCES student (student_id)
                        ON DELETE CASCADE
                )
                """
            )

            # 8. testcase_config依存テーブル: result_execute
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS result_execute (
                    student_id       TEXT NOT NULL,
                    testcase_id      TEXT NOT NULL,
                    is_success       INTEGER NOT NULL,
                    timestamp        DATETIME NOT NULL,
                    error_summary    TEXT,
                    execute_config_mtime DATETIME,
                    output_file_collection_json TEXT,
                    PRIMARY KEY (student_id, testcase_id),
                    FOREIGN KEY (student_id) REFERENCES student (student_id)
                        ON DELETE CASCADE,
                    FOREIGN KEY (testcase_id) REFERENCES testcase_config (testcase_id)
                        ON DELETE CASCADE
                )
                """
            )

            # 9. testcase_config依存テーブル: result_test
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS result_test (
                    student_id       TEXT NOT NULL,
                    testcase_id      TEXT NOT NULL,
                    is_success       INTEGER NOT NULL,
                    timestamp        DATETIME NOT NULL,
                    error_summary    TEXT,
                    test_config_mtime DATETIME,
                    test_result_output_file_collection_json TEXT,
                    failure_reason TEXT,
                    PRIMARY KEY (student_id, testcase_id),
                    FOREIGN KEY (student_id) REFERENCES student (student_id)
                        ON DELETE CASCADE,
                    FOREIGN KEY (testcase_id) REFERENCES testcase_config (testcase_id)
                        ON DELETE CASCADE
                )
                """
            )

            con.commit()
