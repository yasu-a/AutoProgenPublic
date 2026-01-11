import json
import threading
from datetime import datetime
from typing import Dict, Optional

from shared.domain.interface.repository import IStudentStageResultRepository
from shared.domain.model.stage import Stage, StageElement
from shared.domain.model.student_result import (
    AbstractStageResultEntity,
    BuildStageResultEntity,
    CompileStageResultEntity,
    ExecuteStageResultEntity,
    StudentStageStatusEntity,
    StudentStageStatusFlag,
    TestStageResultEntity,
)
from shared.domain.value.identifier import StudentID, TestCaseID
from shared.domain.value.output_file import OutputFileCollection
from shared.domain.value.student_stage_result import (
    TestResultOutputFileCollection
)
from shared.infra.system.project_database import ProjectDatabaseIO
from util.app_logging import create_logger


class _BuildResultHelper:
    _logger = create_logger()

    @classmethod
    def upsert(cls, cursor, entity: BuildStageResultEntity) -> None:
        cursor.execute("""
            INSERT OR REPLACE INTO result_build
            (student_id, is_success, timestamp, error_summary,
             submission_folder_checksum)
            VALUES (?, ?, ?, ?, ?)
        """, (
            str(entity.student_id),
            1 if entity.is_success else 0,
            entity.timestamp,
            entity.error_summary,
            entity.submission_folder_checksum
        ))

    @classmethod
    def fetch(cls, cursor, student_id: StudentID) -> Optional[BuildStageResultEntity]:
        sql = "SELECT * FROM result_build WHERE student_id = ?"
        row = cursor.execute(sql, (str(student_id),)).fetchone()
        if not row:
            return None
        return BuildStageResultEntity(
            student_id=student_id,
            submission_folder_checksum=int(row["submission_folder_checksum"]) if row["submission_folder_checksum"] is not None else None,
            timestamp=row["timestamp"],
            is_success=bool(row["is_success"]),
            error_summary=row["error_summary"]
        )

    @classmethod
    def delete(cls, cursor, student_id: StudentID) -> None:
        cursor.execute(
            "DELETE FROM result_build WHERE student_id = ?",
            (str(student_id),)
        )


class _CompileResultHelper:
    _logger = create_logger()

    @classmethod
    def upsert(cls, cursor, entity: CompileStageResultEntity) -> None:
        cursor.execute("""
            INSERT OR REPLACE INTO result_compile
            (student_id, is_success, timestamp, error_summary, compiler_output)
            VALUES (?, ?, ?, ?, ?)
        """, (
            str(entity.student_id),
            1 if entity.is_success else 0,
            entity.timestamp,
            entity.error_summary,
            entity.output
        ))

    @classmethod
    def fetch(cls, cursor, student_id: StudentID) -> Optional[CompileStageResultEntity]:
        sql = "SELECT * FROM result_compile WHERE student_id = ?"
        row = cursor.execute(sql, (str(student_id),)).fetchone()
        if not row:
            return None
        return CompileStageResultEntity(
            student_id=student_id,
            output=row["compiler_output"],
            timestamp=row["timestamp"],
            is_success=bool(row["is_success"]),
            error_summary=row["error_summary"]
        )

    @classmethod
    def delete(cls, cursor, student_id: StudentID) -> None:
        cursor.execute(
            "DELETE FROM result_compile WHERE student_id = ?",
            (str(student_id),)
        )


class _ExecuteResultHelper:
    _logger = create_logger()

    @classmethod
    def upsert(cls, cursor, entity: ExecuteStageResultEntity) -> None:
        files_json = None
        if entity.output_file_collection:
            files_json = json.dumps(entity.output_file_collection.to_json())

        cursor.execute("""
            INSERT OR REPLACE INTO result_execute
            (student_id, testcase_id, is_success, timestamp, error_summary,
             execute_config_mtime, output_file_collection_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(entity.student_id),
            str(entity.testcase_id),
            1 if entity.is_success else 0,
            entity.timestamp,
            entity.error_summary,
            entity.execute_config_mtime,
            files_json
        ))

    @classmethod
    def fetch(cls, cursor, student_id: StudentID,
              testcase_id: TestCaseID) -> Optional[ExecuteStageResultEntity]:
        sql = "SELECT * FROM result_execute WHERE student_id = ? AND testcase_id = ?"
        row = cursor.execute(
            sql, (str(student_id), str(testcase_id))).fetchone()
        if not row:
            return None

        files = None
        if row["output_file_collection_json"]:
            files = OutputFileCollection.from_json(
                json.loads(row["output_file_collection_json"])
            )

        return ExecuteStageResultEntity(
            student_id=student_id,
            testcase_id=testcase_id,
            execute_config_mtime=row["execute_config_mtime"],
            output_file_collection=files,
            timestamp=row["timestamp"],
            is_success=bool(row["is_success"]),
            error_summary=row["error_summary"]
        )

    @classmethod
    def delete(cls, cursor, student_id: StudentID,
               testcase_id: Optional[TestCaseID]) -> None:
        if testcase_id:
            sql = "DELETE FROM result_execute WHERE student_id = ? AND testcase_id = ?"
            cursor.execute(sql, (str(student_id), str(testcase_id)))
        else:
            sql = "DELETE FROM result_execute WHERE student_id = ?"
            cursor.execute(sql, (str(student_id),))


class _TestResultHelper:
    _logger = create_logger()

    @classmethod
    def upsert(cls, cursor, entity: TestStageResultEntity) -> None:
        files_json = None
        if entity.test_result_output_file_collection:
            files_json = json.dumps(
                entity.test_result_output_file_collection.to_json()
            )

        cursor.execute("""
            INSERT OR REPLACE INTO result_test
            (student_id, testcase_id, is_success, timestamp, error_summary,
             test_config_mtime, test_result_output_file_collection_json, failure_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(entity.student_id),
            str(entity.testcase_id),
            1 if entity.is_success else 0,
            entity.timestamp,
            entity.error_summary,
            entity.test_config_mtime,
            files_json,
            entity.failure_reason
        ))

    @classmethod
    def fetch(cls, cursor, student_id: StudentID,
              testcase_id: TestCaseID) -> Optional[TestStageResultEntity]:
        sql = "SELECT * FROM result_test WHERE student_id = ? AND testcase_id = ?"
        row = cursor.execute(
            sql, (str(student_id), str(testcase_id))).fetchone()
        if not row:
            return None

        files = None
        if row["test_result_output_file_collection_json"]:
            files = TestResultOutputFileCollection.from_json(
                json.loads(row["test_result_output_file_collection_json"])
            )

        return TestStageResultEntity(
            student_id=student_id,
            testcase_id=testcase_id,
            test_config_mtime=row["test_config_mtime"],
            test_result_output_file_collection=files,
            failure_reason=row["failure_reason"],
            timestamp=row["timestamp"],
            is_success=bool(row["is_success"]),
            error_summary=row["error_summary"]
        )

    @classmethod
    def delete(cls, cursor, student_id: StudentID,
               testcase_id: Optional[TestCaseID]) -> None:
        if testcase_id:
            sql = "DELETE FROM result_test WHERE student_id = ? AND testcase_id = ?"
            cursor.execute(sql, (str(student_id), str(testcase_id)))
        else:
            sql = "DELETE FROM result_test WHERE student_id = ?"
            cursor.execute(sql, (str(student_id),))


class StudentStageResultRepository(IStudentStageResultRepository):
    """
    キャッシュ機能を備えた生徒ステージ結果リポジトリ。
    各ステージの結果を独立したテーブルで管理し、スレッドセーフなアクセスを保証します。
    """

    def __init__(self, *, project_database_io: ProjectDatabaseIO):
        self._project_database_io = project_database_io

        # ロックとキャッシュ
        self._lock = threading.RLock()
        self._status_cache: Dict[StudentID, StudentStageStatusEntity] = {}

        self._build = _BuildResultHelper
        self._compile = _CompileResultHelper
        self._execute = _ExecuteResultHelper
        self._test = _TestResultHelper

    def update(self, result: AbstractStageResultEntity) -> None:
        with self._lock:
            with self._project_database_io.connect() as con:
                cur = con.cursor()
                if isinstance(result, BuildStageResultEntity):
                    self._build.upsert(cur, result)
                elif isinstance(result, CompileStageResultEntity):
                    self._compile.upsert(cur, result)
                elif isinstance(result, ExecuteStageResultEntity):
                    self._execute.upsert(cur, result)
                elif isinstance(result, TestStageResultEntity):
                    self._test.upsert(cur, result)
                con.commit()

            # キャッシュの無効化
            if result.student_id in self._status_cache:
                del self._status_cache[result.student_id]

    def get_status(self, student_id: StudentID) -> StudentStageStatusEntity:
        with self._lock:
            # キャッシュのチェック
            if student_id in self._status_cache:
                return self._status_cache[student_id]

            sid_str = str(student_id)
            sql = """
                SELECT 'build' as stage, NULL as tid, is_success, timestamp
                FROM result_build WHERE student_id = ?
                UNION ALL
                SELECT 'compile', NULL, is_success, timestamp
                FROM result_compile WHERE student_id = ?
                UNION ALL
                SELECT 'execute', testcase_id, is_success, timestamp
                FROM result_execute WHERE student_id = ?
                UNION ALL
                SELECT 'test', testcase_id, is_success, timestamp
                FROM result_test WHERE student_id = ?
            """
            with self._project_database_io.connect() as con:
                cur = con.cursor()
                rows = cur.execute(
                    sql, (sid_str, sid_str, sid_str, sid_str)).fetchall()

            build_s = StudentStageStatusFlag.UNFINISHED
            compile_s = StudentStageStatusFlag.UNFINISHED
            exec_s, test_s, max_ts = {}, {}, None

            for row in rows:
                stg, tid, ok, ts = (
                    row["stage"], row["tid"], bool(
                        row["is_success"]), row["timestamp"]
                )
                flag = (
                    StudentStageStatusFlag.FINISHED_SUCCESS if ok
                    else StudentStageStatusFlag.FINISHED_FAILURE
                )
                if max_ts is None or ts > max_ts:
                    max_ts = ts

                if stg == 'build':
                    build_s = flag
                elif stg == 'compile':
                    compile_s = flag
                elif stg == 'execute':
                    exec_s[TestCaseID(tid)] = flag
                elif stg == 'test':
                    test_s[TestCaseID(tid)] = flag

            status = StudentStageStatusEntity(
                student_id, build_s, compile_s, exec_s, test_s, max_ts
            )
            self._status_cache[student_id] = status
            return status

    def get_build_result(self, student_id: StudentID) -> Optional[BuildStageResultEntity]:
        with self._lock:
            with self._project_database_io.connect() as con:
                return self._build.fetch(con.cursor(), student_id)

    def get_compile_result(self, student_id: StudentID) -> Optional[CompileStageResultEntity]:
        with self._lock:
            with self._project_database_io.connect() as con:
                return self._compile.fetch(con.cursor(), student_id)

    def get_execute_result(self, student_id: StudentID,
                           testcase_id: TestCaseID) -> Optional[ExecuteStageResultEntity]:
        with self._lock:
            with self._project_database_io.connect() as con:
                return self._execute.fetch(con.cursor(), student_id, testcase_id)

    def get_test_result(self, student_id: StudentID,
                        testcase_id: TestCaseID) -> Optional[TestStageResultEntity]:
        with self._lock:
            with self._project_database_io.connect() as con:
                return self._test.fetch(con.cursor(), student_id, testcase_id)

    def delete(self, student_id: StudentID, stage: StageElement) -> None:
        with self._lock:
            with self._project_database_io.connect() as con:
                cur = con.cursor()
                if stage.stage == Stage.BUILD:
                    self._build.delete(cur, student_id)
                elif stage.stage == Stage.COMPILE:
                    self._compile.delete(cur, student_id)
                elif stage.stage == Stage.EXECUTE:
                    self._execute.delete(cur, student_id, stage.testcase_id)
                elif stage.stage == Stage.TEST:
                    self._test.delete(cur, student_id, stage.testcase_id)
                con.commit()

            if student_id in self._status_cache:
                del self._status_cache[student_id]
