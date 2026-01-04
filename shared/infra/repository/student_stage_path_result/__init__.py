import json
from datetime import datetime
from typing import Optional

from shared.domain.interface.repository import IStudentStageResultRepository
from shared.domain.model.stage import Stage, StageElement
from shared.domain.model.student_result import \
    StudentStageStatusEntity, StudentStageStatusFlag, \
    AbstractStageResultEntity, BuildStageResultEntity, CompileStageResultEntity, \
    ExecuteStageResultEntity, TestStageResultEntity
from shared.domain.value.identifier import StudentID, TestCaseID
from shared.domain.value.output_file import OutputFileCollection
from shared.domain.value.student_stage_result import TestResultOutputFileCollection
from shared.infra.system.project_database import ProjectDatabaseIO
from util.app_logging import create_logger


# 新しいテーブル設計用のHelperクラス群

class _StageResultHeaderHelper:
    """共通ヘッダーテーブル用Helper"""

    _DB_COMMON_ID = "__COMMON__"

    def create_table_if_not_exists(self, cursor) -> None:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS student_stage_result_header
            (
                student_id  TEXT NOT NULL,
                stage       TEXT NOT NULL,
                testcase_id TEXT NOT NULL DEFAULT '__COMMON__',
                is_success  INTEGER NOT NULL,
                timestamp   DATETIME NOT NULL,
                error_summary TEXT,
                PRIMARY KEY (student_id, stage, testcase_id),
                FOREIGN KEY (student_id) REFERENCES student (student_id),
                FOREIGN KEY (testcase_id) REFERENCES testcase_config (testcase_id)
            )
            """
        )

    def upsert(self, cursor, student_id: StudentID, stage: Stage, testcase_id: str,
               is_success: bool, timestamp: datetime, error_summary: str | None) -> None:
        cursor.execute(
            """
            INSERT OR REPLACE INTO student_stage_result_header
            (student_id, stage, testcase_id, is_success, timestamp, error_summary)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (str(student_id), stage.value, testcase_id,
             1 if is_success else 0, timestamp, error_summary)
        )

    def fetch_status(self, cursor, student_id: StudentID) -> tuple[dict, datetime | None]:
        cursor.execute(
            """
            SELECT stage, testcase_id, is_success, timestamp
            FROM student_stage_result_header
            WHERE student_id = ?
            """,
            (str(student_id),)
        )
        rows = cursor.fetchall()

        build_status = None
        compile_status = None
        execute_status: dict[TestCaseID, StudentStageStatusFlag] = {}
        test_status: dict[TestCaseID, StudentStageStatusFlag] = {}
        max_timestamp = None

        for row in rows:
            stage_str = row["stage"]
            testcase_id_str = row["testcase_id"]
            is_success = bool(row["is_success"])
            ts = row["timestamp"]

            if max_timestamp is None or ts > max_timestamp:
                max_timestamp = ts

            flag = StudentStageStatusFlag.FINISHED_SUCCESS if is_success else StudentStageStatusFlag.FINISHED_FAILURE

            if testcase_id_str == self._DB_COMMON_ID:
                # BUILD or COMPILE
                if stage_str == Stage.BUILD.value:
                    build_status = flag
                elif stage_str == Stage.COMPILE.value:
                    compile_status = flag
            else:
                # EXECUTE or TEST
                testcase_id = TestCaseID(testcase_id_str)
                if stage_str == Stage.EXECUTE.value:
                    execute_status[testcase_id] = flag
                elif stage_str == Stage.TEST.value:
                    test_status[testcase_id] = flag

        return {
            "build": build_status,
            "compile": compile_status,
            "execute": execute_status,
            "test": test_status
        }, max_timestamp

    def fetch_header(self, cursor, student_id: StudentID, stage: Stage, testcase_id: str) -> dict | None:
        cursor.execute(
            """
            SELECT is_success, timestamp, error_summary
            FROM student_stage_result_header
            WHERE student_id = ? AND stage = ? AND testcase_id = ?
            """,
            (str(student_id), stage.value, testcase_id)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return {
            "is_success": bool(row["is_success"]),
            "timestamp": row["timestamp"],
            "error_summary": row["error_summary"]
        }

    def delete(self, cursor, student_id: StudentID, stage: Stage, testcase_id: str) -> None:
        """ヘッダーを削除（CASCADEで詳細も削除される）"""
        cursor.execute(
            """
            DELETE FROM student_stage_result_header
            WHERE student_id = ? AND stage = ? AND testcase_id = ?
            """,
            (str(student_id), stage.value, testcase_id)
        )


class _BuildResultDetailHelper:
    """BUILD詳細テーブル用Helper"""

    def create_table_if_not_exists(self, cursor) -> None:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS result_detail_build
            (
                student_id  TEXT NOT NULL,
                stage       TEXT NOT NULL DEFAULT 'build',
                testcase_id TEXT NOT NULL DEFAULT '__COMMON__',
                submission_folder_checksum TEXT,
                PRIMARY KEY (student_id, stage, testcase_id),
                FOREIGN KEY (student_id, stage, testcase_id)
                    REFERENCES student_stage_result_header (student_id, stage, testcase_id)
                    ON DELETE CASCADE
            )
            """
        )

    def upsert(self, cursor, student_id: StudentID, checksum: str | None) -> None:
        cursor.execute(
            """
            INSERT OR REPLACE INTO result_detail_build
            (student_id, stage, testcase_id, submission_folder_checksum)
            VALUES (?, 'build', '__COMMON__', ?)
            """,
            (str(student_id), checksum)
        )

    def fetch(self, cursor, student_id: StudentID) -> dict | None:
        cursor.execute(
            """
            SELECT submission_folder_checksum
            FROM result_detail_build
            WHERE student_id = ?
            """,
            (str(student_id),)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return {"submission_folder_checksum": row["submission_folder_checksum"]}


class _CompileResultDetailHelper:
    """COMPILE詳細テーブル用Helper"""

    def create_table_if_not_exists(self, cursor) -> None:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS result_detail_compile
            (
                student_id  TEXT NOT NULL,
                stage       TEXT NOT NULL DEFAULT 'compile',
                testcase_id TEXT NOT NULL DEFAULT '__COMMON__',
                compiler_output TEXT,
                PRIMARY KEY (student_id, stage, testcase_id),
                FOREIGN KEY (student_id, stage, testcase_id)
                    REFERENCES student_stage_result_header (student_id, stage, testcase_id)
                    ON DELETE CASCADE
            )
            """
        )

    def upsert(self, cursor, student_id: StudentID, compiler_output: str | None) -> None:
        cursor.execute(
            """
            INSERT OR REPLACE INTO result_detail_compile
            (student_id, stage, testcase_id, compiler_output)
            VALUES (?, 'compile', '__COMMON__', ?)
            """,
            (str(student_id), compiler_output)
        )

    def fetch(self, cursor, student_id: StudentID) -> dict | None:
        cursor.execute(
            """
            SELECT compiler_output
            FROM result_detail_compile
            WHERE student_id = ?
            """,
            (str(student_id),)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return {"compiler_output": row["compiler_output"]}


class _ExecuteResultDetailHelper:
    """EXECUTE詳細テーブル用Helper"""

    def create_table_if_not_exists(self, cursor) -> None:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS result_detail_execute
            (
                student_id  TEXT NOT NULL,
                stage       TEXT NOT NULL DEFAULT 'execute',
                testcase_id TEXT NOT NULL,
                execute_config_mtime DATETIME,
                output_files_json TEXT,
                PRIMARY KEY (student_id, stage, testcase_id),
                FOREIGN KEY (student_id, stage, testcase_id)
                    REFERENCES student_stage_result_header (student_id, stage, testcase_id)
                    ON DELETE CASCADE,
                FOREIGN KEY (testcase_id) REFERENCES testcase_config (testcase_id)
            )
            """
        )

    def upsert(self, cursor, student_id: StudentID, testcase_id: TestCaseID,
               execute_config_mtime: datetime | None, output_file_collection: OutputFileCollection | None) -> None:
        output_files_json = None
        if output_file_collection is not None:
            output_files_json = json.dumps(output_file_collection.to_json())

        cursor.execute(
            """
            INSERT OR REPLACE INTO result_detail_execute
            (student_id, stage, testcase_id, execute_config_mtime, output_files_json)
            VALUES (?, 'execute', ?, ?, ?)
            """,
            (str(student_id), str(testcase_id),
             execute_config_mtime, output_files_json)
        )

    def fetch(self, cursor, student_id: StudentID, testcase_id: TestCaseID) -> dict | None:
        cursor.execute(
            """
            SELECT execute_config_mtime, output_files_json
            FROM result_detail_execute
            WHERE student_id = ? AND testcase_id = ?
            """,
            (str(student_id), str(testcase_id))
        )
        row = cursor.fetchone()
        if row is None:
            return None

        output_file_collection = None
        if row["output_files_json"] is not None:
            output_file_collection = OutputFileCollection.from_json(
                json.loads(row["output_files_json"]))

        return {
            "execute_config_mtime": row["execute_config_mtime"],
            "output_file_collection": output_file_collection
        }


class _TestResultDetailHelper:
    """TEST詳細テーブル用Helper"""

    def create_table_if_not_exists(self, cursor) -> None:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS result_detail_test
            (
                student_id  TEXT NOT NULL,
                stage       TEXT NOT NULL DEFAULT 'test',
                testcase_id TEXT NOT NULL,
                test_config_mtime DATETIME,
                test_result_output_files_json TEXT,
                failure_reason TEXT,
                PRIMARY KEY (student_id, stage, testcase_id),
                FOREIGN KEY (student_id, stage, testcase_id)
                    REFERENCES student_stage_result_header (student_id, stage, testcase_id)
                    ON DELETE CASCADE,
                FOREIGN KEY (testcase_id) REFERENCES testcase_config (testcase_id)
            )
            """
        )

    def upsert(self, cursor, student_id: StudentID, testcase_id: TestCaseID,
               test_config_mtime: datetime | None, test_result_output_file_collection: TestResultOutputFileCollection | None,
               failure_reason: str | None) -> None:
        test_result_output_files_json = None
        if test_result_output_file_collection is not None:
            test_result_output_files_json = json.dumps(
                test_result_output_file_collection.to_json())

        cursor.execute(
            """
            INSERT OR REPLACE INTO result_detail_test
            (student_id, stage, testcase_id, test_config_mtime, test_result_output_files_json, failure_reason)
            VALUES (?, 'test', ?, ?, ?, ?)
            """,
            (str(student_id), str(testcase_id), test_config_mtime,
             test_result_output_files_json, failure_reason)
        )

    def fetch(self, cursor, student_id: StudentID, testcase_id: TestCaseID) -> dict | None:
        cursor.execute(
            """
            SELECT test_config_mtime, test_result_output_files_json, failure_reason
            FROM result_detail_test
            WHERE student_id = ? AND testcase_id = ?
            """,
            (str(student_id), str(testcase_id))
        )
        row = cursor.fetchone()
        if row is None:
            return None

        test_result_output_file_collection = None
        if row["test_result_output_files_json"] is not None:
            test_result_output_file_collection = TestResultOutputFileCollection.from_json(
                json.loads(row["test_result_output_files_json"]))

        return {
            "test_config_mtime": row["test_config_mtime"],
            "test_result_output_file_collection": test_result_output_file_collection,
            "failure_reason": row["failure_reason"]
        }


class StudentStageResultRepository(IStudentStageResultRepository):
    def __init__(
            self,
            *,
            project_database_io: ProjectDatabaseIO,
    ):
        self._project_database_io = project_database_io
        self._logger = create_logger()

        self._header_helper = _StageResultHeaderHelper()
        self._build_helper = _BuildResultDetailHelper()
        self._compile_helper = _CompileResultDetailHelper()
        self._execute_helper = _ExecuteResultDetailHelper()
        self._test_helper = _TestResultDetailHelper()

        self._create_tables_if_not_exists()

    def _create_tables_if_not_exists(self) -> None:
        with self._project_database_io.connect() as con:
            cur = con.cursor()
            self._header_helper.create_table_if_not_exists(cur)
            self._build_helper.create_table_if_not_exists(cur)
            self._compile_helper.create_table_if_not_exists(cur)
            self._execute_helper.create_table_if_not_exists(cur)
            self._test_helper.create_table_if_not_exists(cur)
            con.commit()

    def get_build_result(self, student_id: StudentID) -> Optional[BuildStageResultEntity]:
        with self._project_database_io.connect() as con:
            cur = con.cursor()
            header = self._header_helper.fetch_header(
                cur, student_id, Stage.BUILD, _StageResultHeaderHelper._DB_COMMON_ID)
            if header is None:
                return None
            detail = self._build_helper.fetch(cur, student_id)

            # detail がない場合でも header があれば生成可能（仕様によるが今回は許容する）
            checksum = detail["submission_folder_checksum"] if detail else None

            return BuildStageResultEntity(
                student_id=student_id,
                submission_folder_checksum=checksum,
                timestamp=header["timestamp"],
                is_success=header["is_success"],
                error_summary=header["error_summary"],
            )

    def get_compile_result(self, student_id: StudentID) -> Optional[CompileStageResultEntity]:
        with self._project_database_io.connect() as con:
            cur = con.cursor()
            header = self._header_helper.fetch_header(
                cur, student_id, Stage.COMPILE, _StageResultHeaderHelper._DB_COMMON_ID)
            if header is None:
                return None
            detail = self._compile_helper.fetch(cur, student_id)
            output = detail["compiler_output"] if detail else None

            return CompileStageResultEntity(
                student_id=student_id,
                output=output,
                timestamp=header["timestamp"],
                is_success=header["is_success"],
                error_summary=header["error_summary"],
            )

    def get_execute_result(self, student_id: StudentID, testcase_id: TestCaseID) -> Optional[ExecuteStageResultEntity]:
        with self._project_database_io.connect() as con:
            cur = con.cursor()
            header = self._header_helper.fetch_header(
                cur, student_id, Stage.EXECUTE, str(testcase_id))
            if header is None:
                return None
            detail = self._execute_helper.fetch(cur, student_id, testcase_id)

            execute_config_mtime = detail["execute_config_mtime"] if detail else None
            output_file_collection = detail["output_file_collection"] if detail else None

            return ExecuteStageResultEntity(
                student_id=student_id,
                testcase_id=testcase_id,
                execute_config_mtime=execute_config_mtime,
                output_file_collection=output_file_collection,
                timestamp=header["timestamp"],
                is_success=header["is_success"],
                error_summary=header["error_summary"],
            )

    def get_test_result(self, student_id: StudentID, testcase_id: TestCaseID) -> Optional[TestStageResultEntity]:
        with self._project_database_io.connect() as con:
            cur = con.cursor()
            header = self._header_helper.fetch_header(
                cur, student_id, Stage.TEST, str(testcase_id))
            if header is None:
                return None
            detail = self._test_helper.fetch(cur, student_id, testcase_id)

            test_config_mtime = detail["test_config_mtime"] if detail else None
            test_result_output_file_collection = detail["test_result_output_file_collection"] if detail else None
            failure_reason = detail["failure_reason"] if detail else None

            return TestStageResultEntity(
                student_id=student_id,
                testcase_id=testcase_id,
                test_config_mtime=test_config_mtime,
                test_result_output_file_collection=test_result_output_file_collection,
                failure_reason=failure_reason,
                timestamp=header["timestamp"],
                is_success=header["is_success"],
                error_summary=header["error_summary"],
            )

    def update(self, result: AbstractStageResultEntity) -> None:
        student_id = result.student_id
        stage = result.stage
        testcase_id_str = str(
            result.testcase_id) if result.testcase_id else _StageResultHeaderHelper._DB_COMMON_ID

        with self._project_database_io.connect() as con:
            cur = con.cursor()

            # ヘッダーを保存
            self._header_helper.upsert(
                cur, student_id, stage, testcase_id_str,
                result.is_success, result.timestamp, result.error_summary
            )

            # 詳細テーブルへの保存
            if isinstance(result, BuildStageResultEntity):
                self._build_helper.upsert(
                    cur, student_id, result.submission_folder_checksum)
            elif isinstance(result, CompileStageResultEntity):
                self._compile_helper.upsert(cur, student_id, result.output)
            elif isinstance(result, ExecuteStageResultEntity):
                assert result.testcase_id is not None
                self._execute_helper.upsert(
                    cur, student_id, result.testcase_id,
                    result.execute_config_mtime, result.output_file_collection
                )
            elif isinstance(result, TestStageResultEntity):
                assert result.testcase_id is not None
                self._test_helper.upsert(
                    cur, student_id, result.testcase_id,
                    result.test_config_mtime, result.test_result_output_file_collection,
                    result.failure_reason
                )

            con.commit()

    def get_status(self, student_id: StudentID) -> StudentStageStatusEntity:
        """ステータス情報を取得"""
        with self._project_database_io.connect() as con:
            cur = con.cursor()
            status_dict, max_timestamp = self._header_helper.fetch_status(
                cur, student_id)
            return StudentStageStatusEntity(
                student_id=student_id,
                build_status=status_dict["build"] or StudentStageStatusFlag.UNFINISHED,
                compile_status=status_dict["compile"] or StudentStageStatusFlag.UNFINISHED,
                execute_status=status_dict["execute"],
                test_status=status_dict["test"],
                timestamp=max_timestamp,
            )

    def delete(self, student_id: StudentID, stage: StageElement) -> None:
        """指定されたステージの結果を削除"""
        testcase_id_str = str(
            stage.testcase_id) if stage.testcase_id else _StageResultHeaderHelper._DB_COMMON_ID
        with self._project_database_io.connect() as con:
            cur = con.cursor()
            self._header_helper.delete(
                cur, student_id, stage.stage, testcase_id_str)
            con.commit()
