import json
from abc import abstractmethod, ABC
from contextlib import contextmanager
from datetime import datetime

from domain.errors import RepositoryItemNotFoundError
from domain.models.output_file import OutputFileMapping
from domain.models.stages import (
    BuildStage,
    CompileStage,
    ExecuteStage,
    TestStage, AbstractStage,
)
from domain.models.student_stage_result import (
    AbstractStudentStageResult,
    BuildFailureStudentStageResult,
    BuildSuccessStudentStageResult,
    CompileFailureStudentStageResult,
    CompileSuccessStudentStageResult,
    ExecuteFailureStudentStageResult,
    ExecuteSuccessStudentStageResult,
    TestFailureStudentStageResult,
    TestSuccessStudentStageResult,
    TestResultOutputFileMapping,
)
from domain.models.values import StudentID, TestCaseID
from infra.io.project_database import ProjectDatabaseIO
from infra.lock.student import StudentLockServer


class _AbstractResultRepositoryHelper(ABC):
    # 扱うStageResultの型
    # リストの型のいずれかに当てはまる場合にこのヘルパーでハンドルされる
    _handle_result_type: tuple = ...

    # 扱うStage
    _handle_stage_type: type[AbstractStage] = ...

    def __init__(self, *, project_database_io: ProjectDatabaseIO):
        self._project_database_io = project_database_io
        self._create_table_if_not_exists()

    def is_acceptable_result_type(self, result: AbstractStudentStageResult) -> bool:
        return isinstance(result, self._handle_result_type)

    def is_acceptable_stage(self, stage: AbstractStage) -> bool:
        return isinstance(stage, self._handle_stage_type)

    @abstractmethod
    def _create_table_if_not_exists(self):
        raise NotImplementedError()

    @abstractmethod
    def put(self, result: AbstractStudentStageResult) -> None:
        raise NotImplementedError()

    @abstractmethod
    def exists(self, student_id: StudentID, stage: AbstractStage) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def get(self, student_id: StudentID, stage: AbstractStage) -> AbstractStudentStageResult:
        raise NotImplementedError()

    @abstractmethod
    def delete(self, student_id: StudentID, stage: AbstractStage) -> None:
        raise NotImplementedError()


class _BuildResultRepositoryHelper(_AbstractResultRepositoryHelper):
    _handle_result_type = (BuildSuccessStudentStageResult, BuildFailureStudentStageResult)
    _handle_stage_type = BuildStage

    """
    BuildSuccessStudentStageResult:
        - student_id: StudentIDt
        - submission_folder_checksum: int
    BuildFailureStudentStageResult
        - student_id: StudentID
        - reason: str
    """

    def _create_table_if_not_exists(self):
        with self._project_database_io.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS student_build_result
                (
                    student_id                 TEXT PRIMARY KEY,
                    submission_folder_checksum UNSIGNED INTEGER,
                    reason                     TEXT,
                    FOREIGN KEY (student_id) REFERENCES student (student_id)
                )
                """
            )
            conn.commit()

    def put(
            self,
            result: AbstractStudentStageResult,
    ) -> None:
        with self._project_database_io.connect() as con:
            cur = con.cursor()
            if isinstance(result, BuildSuccessStudentStageResult):
                cur.execute(
                    """
                    INSERT OR REPLACE INTO student_build_result
                    (student_id, submission_folder_checksum, reason)
                    VALUES (?, ?, NULL)
                    """,
                    (str(result.student_id), result.submission_folder_checksum),
                )
            elif isinstance(result, BuildFailureStudentStageResult):
                cur.execute(
                    """
                    INSERT OR REPLACE INTO student_build_result
                    (student_id, submission_folder_checksum, reason)
                    VALUES (?, NULL, ?)
                    """,
                    (str(result.student_id), result.reason),
                )
            else:
                assert False, type(result)
            con.commit()

    def exists(
            self,
            student_id: StudentID,
            stage: AbstractStage,
    ) -> bool:
        assert isinstance(stage, BuildStage), stage
        with self._project_database_io.connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                SELECT EXISTS (SELECT 1
                               FROM student_build_result
                               WHERE student_id = ?)
                """,
                (str(student_id),),
            )
            return bool(cur.fetchone()[0])

    def get(
            self,
            student_id: StudentID,
            stage: AbstractStage,
    ) -> AbstractStudentStageResult:
        assert isinstance(stage, BuildStage), stage
        with self._project_database_io.connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                SELECT *
                FROM student_build_result
                WHERE student_id = ?
                """,
                (str(student_id),),
            )
            row = cur.fetchone()
            if row is None:
                raise RepositoryItemNotFoundError(
                    f"Build result for student {student_id} not found"
                )
            if row["reason"] is None:
                return BuildSuccessStudentStageResult.create_instance(
                    student_id=student_id,
                    submission_folder_checksum=row["submission_folder_checksum"],
                )
            else:
                return BuildFailureStudentStageResult.create_instance(
                    student_id=student_id,
                    reason=row["reason"],
                )

    def delete(
            self,
            student_id: StudentID,
            stage: AbstractStage,
    ) -> None:
        assert isinstance(stage, BuildStage), stage
        with self._project_database_io.connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                DELETE
                FROM student_build_result
                WHERE student_id = ?
                """,
                (str(student_id),),
            )
            if cur.rowcount == 0:
                raise RepositoryItemNotFoundError(
                    f"Build result for student {student_id} not found"
                )
            con.commit()


class _CompileResultRepositoryHelper(_AbstractResultRepositoryHelper):
    _handle_result_type = (CompileSuccessStudentStageResult, CompileFailureStudentStageResult)
    _handle_stage_type = CompileStage

    """
    CompileSuccessStudentStageResult:
        - student_id: StudentID
        - output: str
    CompileFailureStudentStageResult
        - student_id: StudentID
        - reason: str
        - output: str
    """

    def _create_table_if_not_exists(self):
        with self._project_database_io.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS student_compile_result
                (
                    student_id TEXT PRIMARY KEY,
                    output     TEXT NOT NULL,
                    reason     TEXT,
                    FOREIGN KEY (student_id) REFERENCES student (student_id)
                )
                """
            )
            conn.commit()

    def put(
            self,
            result: AbstractStudentStageResult,
    ) -> None:
        with self._project_database_io.connect() as con:
            cur = con.cursor()
            if isinstance(result, CompileSuccessStudentStageResult):
                cur.execute(
                    """
                    INSERT OR REPLACE INTO student_compile_result
                    (student_id, output, reason)
                    VALUES (?, ?, NULL)
                    """,
                    (str(result.student_id), result.output),
                )
            elif isinstance(result, CompileFailureStudentStageResult):
                cur.execute(
                    """
                    INSERT OR REPLACE INTO student_compile_result
                    (student_id, output, reason)
                    VALUES (?, ?, ?)
                    """,
                    (str(result.student_id), result.output, result.reason),
                )
            else:
                assert False, type(result)
            con.commit()

    def exists(
            self,
            student_id: StudentID,
            stage: AbstractStage,
    ) -> bool:
        assert isinstance(stage, CompileStage), stage
        with self._project_database_io.connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                SELECT EXISTS (SELECT 1
                               FROM student_compile_result
                               WHERE student_id = ?)
                """,
                (str(student_id),),
            )
            return bool(cur.fetchone()[0])

    def get(
            self,
            student_id: StudentID,
            stage: AbstractStage,
    ) -> AbstractStudentStageResult:
        assert isinstance(stage, CompileStage), stage
        with self._project_database_io.connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                SELECT *
                FROM student_compile_result
                WHERE student_id = ?
                """,
                (str(student_id),),
            )
            row = cur.fetchone()
            if row is None:
                raise RepositoryItemNotFoundError(
                    f"Compile result for student {student_id} not found"
                )
            if row["reason"] is None:
                return CompileSuccessStudentStageResult.create_instance(
                    student_id=student_id,
                    output=row["output"],
                )
            else:
                return CompileFailureStudentStageResult.create_instance(
                    student_id=student_id,
                    reason=row["reason"],
                    output=row["output"],  # 失敗時もoutputを持つ
                )

    def delete(
            self,
            student_id: StudentID,
            stage: AbstractStage,
    ) -> None:
        assert isinstance(stage, CompileStage), stage
        with self._project_database_io.connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                DELETE
                FROM student_compile_result
                WHERE student_id = ?
                """,
                (str(student_id),),
            )
            if cur.rowcount == 0:
                raise RepositoryItemNotFoundError(
                    f"Compile result for student {student_id} not found"
                )
            con.commit()


class _ExecuteResultRepositoryHelper(_AbstractResultRepositoryHelper):
    _handle_result_type = (ExecuteSuccessStudentStageResult, ExecuteFailureStudentStageResult)
    _handle_stage_type = ExecuteStage

    """
    ExecuteSuccessStudentStageResult:
        - student_id: StudentID
        - stage.testcase_id: TestCaseID
        - execute_config_mtime: datetime (DATETIME in DB)
        - output_files: OutputFileMapping (JSON string)
    ExecuteFailureStudentStageResult
        - student_id: StudentID
        - stage.testcase_id: TestCaseID
        - reason: str
    """

    def _create_table_if_not_exists(self):
        with self._project_database_io.connect() as conn:
            cur = conn.cursor()
            # FIXME: output_filesをjsonとしてDBに書きこんでいる
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS student_execute_result
                (
                    student_id           TEXT,
                    testcase_id          TEXT,
                    execute_config_mtime DATETIME,
                    output_files_json    TEXT,
                    reason               TEXT,
                    PRIMARY KEY (student_id, testcase_id),
                    FOREIGN KEY (student_id) REFERENCES student (student_id)
                )
                """
            )
            # TODO: testcaseテーブルを作ってtestcase_idをFKにする
            conn.commit()

    def put(
            self,
            result: AbstractStudentStageResult,
    ) -> None:
        with self._project_database_io.connect() as con:
            cur = con.cursor()
            assert isinstance(result.stage, ExecuteStage), type(result.stage)
            if isinstance(result, ExecuteSuccessStudentStageResult):
                cur.execute(
                    """
                    INSERT OR REPLACE INTO student_execute_result
                    (student_id, testcase_id, execute_config_mtime, output_files_json, reason)
                    VALUES (?, ?, ?, ?, NULL)
                    """,
                    (
                        str(result.student_id),
                        str(result.stage.testcase_id),
                        result.execute_config_mtime,
                        json.dumps(result.output_files.to_json()),
                    ),
                )
            elif isinstance(result, ExecuteFailureStudentStageResult):
                cur.execute(
                    """
                    INSERT OR REPLACE INTO student_execute_result
                    (student_id, testcase_id, execute_config_mtime, output_files_json, reason)
                    VALUES (?, ?, NULL, NULL, ?)
                    """,
                    (
                        str(result.student_id),
                        str(result.stage.testcase_id),
                        result.reason,
                    ),
                )
            else:
                assert False, type(result)
            con.commit()

    def exists(
            self,
            student_id: StudentID,
            stage: AbstractStage,
    ) -> bool:
        assert isinstance(stage, ExecuteStage), stage
        with self._project_database_io.connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                SELECT EXISTS (SELECT 1
                               FROM student_execute_result
                               WHERE student_id = ?
                                 AND testcase_id = ?)
                """,
                (str(student_id), str(stage.testcase_id)),
            )
            return bool(cur.fetchone()[0])

    def get(
            self,
            student_id: StudentID,
            stage: AbstractStage,
    ) -> AbstractStudentStageResult:
        assert isinstance(stage, ExecuteStage), stage
        with self._project_database_io.connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                SELECT *
                FROM student_execute_result
                WHERE student_id = ?
                  AND testcase_id = ?
                """,
                (str(student_id), str(stage.testcase_id)),
            )
            row = cur.fetchone()
            if row is None:
                raise RepositoryItemNotFoundError(
                    f"Execute result for student {student_id}, testcase {stage.testcase_id} not found"
                )

            if row["reason"] is None:
                return ExecuteSuccessStudentStageResult.create_instance(
                    student_id=student_id,
                    testcase_id=TestCaseID(row["testcase_id"]),
                    execute_config_mtime=row["execute_config_mtime"],
                    output_files=OutputFileMapping.from_json(json.loads(row["output_files_json"])),
                )
            else:
                return ExecuteFailureStudentStageResult.create_instance(
                    student_id=student_id,
                    testcase_id=TestCaseID(row["testcase_id"]),
                    reason=row["reason"],
                )

    def delete(
            self,
            student_id: StudentID,
            stage: AbstractStage,
    ) -> None:
        assert isinstance(stage, ExecuteStage), stage
        with self._project_database_io.connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                DELETE
                FROM student_execute_result
                WHERE student_id = ?
                  AND testcase_id = ?
                """,
                (str(student_id), str(stage.testcase_id)),
            )
            if cur.rowcount == 0:
                raise RepositoryItemNotFoundError(
                    f"Execute result for student {student_id}, testcase {stage.testcase_id} not found"
                )
            con.commit()


class _TestResultRepositoryHelper(_AbstractResultRepositoryHelper):
    _handle_result_type = (TestSuccessStudentStageResult, TestFailureStudentStageResult)
    _handle_stage_type = TestStage

    """
    TestSuccessStudentStageResult:
        - student_id: StudentID
        - stage.testcase_id: TestCaseID
        - test_config_mtime: datetime (DATETIME in DB)
        - test_result_output_files: TestResultOutputFileMapping (JSON string)
    TestFailureStudentStageResult
        - student_id: StudentID
        - stage.testcase_id: TestCaseID
        - reason: str
    """

    def _create_table_if_not_exists(self):
        with self._project_database_io.connect() as conn:
            cur = conn.cursor()
            # FIXME: output_filesをjsonとしてDBに書きこんでいる
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS student_test_result
                (
                    student_id                    TEXT NOT NULL,
                    testcase_id                   TEXT NOT NULL,
                    test_config_mtime             DATETIME,
                    test_result_output_files_json TEXT,
                    reason                        TEXT,
                    PRIMARY KEY (student_id, testcase_id),
                    FOREIGN KEY (student_id) REFERENCES student (student_id)
                )
                """
            )
            # TODO: testcaseテーブルを作ってtestcase_idをFKにする (Executeと同様)
            conn.commit()

    def put(
            self,
            result: AbstractStudentStageResult,
    ) -> None:
        with self._project_database_io.connect() as con:
            cur = con.cursor()
            assert isinstance(result.stage, TestStage), type(result.stage)
            if isinstance(result, TestSuccessStudentStageResult):
                cur.execute(
                    """
                    INSERT OR REPLACE INTO student_test_result
                    (student_id, testcase_id, test_config_mtime, test_result_output_files_json, reason)
                    VALUES (?, ?, ?, ?, NULL)
                    """,
                    (
                        str(result.student_id),
                        str(result.stage.testcase_id),
                        result.test_config_mtime,
                        json.dumps(result.test_result_output_files.to_json()),
                    ),
                )
            elif isinstance(result, TestFailureStudentStageResult):
                cur.execute(
                    """
                    INSERT OR REPLACE INTO student_test_result
                    (student_id, testcase_id, test_config_mtime, test_result_output_files_json, reason)
                    VALUES (?, ?, NULL, NULL, ?)
                    """,
                    (
                        str(result.student_id),
                        str(result.stage.testcase_id),
                        result.reason,
                    ),
                )
            else:
                assert False, type(result)
            con.commit()

    def exists(
            self,
            student_id: StudentID,
            stage: AbstractStage,
    ) -> bool:
        assert isinstance(stage, TestStage), stage
        with self._project_database_io.connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                SELECT EXISTS (SELECT 1
                               FROM student_test_result
                               WHERE student_id = ?
                                 AND testcase_id = ?)
                """,
                (str(student_id), str(stage.testcase_id)),
            )
            return bool(cur.fetchone()[0])

    def get(
            self,
            student_id: StudentID,
            stage: AbstractStage,
    ) -> AbstractStudentStageResult:
        assert isinstance(stage, TestStage), stage
        with self._project_database_io.connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                SELECT *
                FROM student_test_result
                WHERE student_id = ?
                  AND testcase_id = ?
                """,
                (str(student_id), str(stage.testcase_id)),
            )
            row = cur.fetchone()
            if row is None:
                raise RepositoryItemNotFoundError(
                    f"Test result for student {student_id}, testcase {stage.testcase_id} not found"
                )

            if row["reason"] is None:
                return TestSuccessStudentStageResult.create_instance(
                    student_id=student_id,
                    testcase_id=TestCaseID(row["testcase_id"]),
                    test_config_mtime=row["test_config_mtime"],
                    test_result_output_files=TestResultOutputFileMapping.from_json(
                        json.loads(row["test_result_output_files_json"])),
                )
            else:
                return TestFailureStudentStageResult.create_instance(
                    student_id=student_id,
                    testcase_id=TestCaseID(row["testcase_id"]),
                    reason=row["reason"],
                )

    def delete(
            self,
            student_id: StudentID,
            stage: AbstractStage,
    ) -> None:
        assert isinstance(stage, TestStage), stage
        with self._project_database_io.connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                DELETE
                FROM student_test_result
                WHERE student_id = ?
                  AND testcase_id = ?
                """,
                (str(student_id), str(stage.testcase_id)),
            )
            if cur.rowcount == 0:
                raise RepositoryItemNotFoundError(
                    f"Test result for student {student_id}, testcase {stage.testcase_id} not found"
                )
            con.commit()


class _ResultTimestampRepositoryHelper:
    def __init__(self, *, project_database_io: ProjectDatabaseIO):
        self._project_database_io = project_database_io
        self._create_table_if_not_exists()

        self._cache = {}

    def _create_table_if_not_exists(self):
        with self._project_database_io.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS student_result_timestamp
                (
                    student_id TEXT PRIMARY KEY,
                    timestamp  DATETIME NOT NULL,
                    FOREIGN KEY (student_id) REFERENCES student (student_id)
                )
                """
            )
            conn.commit()

    def update(self, student_id: StudentID) -> None:
        """
        指定された生徒IDの現在の時刻を記録（または更新）します。
        """
        timestamp = datetime.now()  # 現在時刻を取得
        self._cache[student_id] = timestamp
        with self._project_database_io.connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                INSERT OR REPLACE INTO student_result_timestamp (student_id, timestamp)
                VALUES (?, ?)
                """,
                (str(student_id), timestamp),
            )
            con.commit()

    def get(self, student_id: StudentID) -> datetime | None:
        """
        指定された生徒IDの記録された時刻を取得します。
        記録がない場合は None を返します。
        """
        if student_id not in self._cache:
            with self._project_database_io.connect() as con:
                cur = con.cursor()
                cur.execute(
                    """
                    SELECT timestamp
                    FROM student_result_timestamp
                    WHERE student_id = ?
                    """,
                    (str(student_id),),
                )
                row = cur.fetchone()
                if row is None:
                    timestamp = None
                else:
                    timestamp = row["timestamp"]
            self._cache[student_id] = timestamp
        return self._cache[student_id]


# プロジェクト内ステートフル:
#  - 自身が_create_table_if_not_existsをインスタンス生成時に実行するため
#  - 各Helperが_create_table_if_not_existsをインスタンス生成時に実行するため
#  - student_lock_serverを保持するため
#  - timestamp_repo_helperがキャッシュを持つため
class StudentStageResultRepository:
    def __init__(
            self,
            *,
            project_database_io: ProjectDatabaseIO,
    ):
        self._project_database_io = project_database_io

        self._student_lock_server = StudentLockServer()

        self._result_repo_helpers = [
            _BuildResultRepositoryHelper(
                project_database_io=self._project_database_io,
            ),
            _CompileResultRepositoryHelper(
                project_database_io=self._project_database_io,
            ),
            _ExecuteResultRepositoryHelper(
                project_database_io=self._project_database_io,
            ),
            _TestResultRepositoryHelper(
                project_database_io=self._project_database_io,
            ),
        ]
        self._timestamp_repo_helper = _ResultTimestampRepositoryHelper(
            project_database_io=self._project_database_io,
        )

    @contextmanager
    def __lock(self, student_id: StudentID):
        self._student_lock_server[student_id].lock()
        try:
            yield
        finally:
            self._student_lock_server[student_id].unlock()

    def _find_acceptable_repo_helper(
            self,
            result_or_stage: AbstractStudentStageResult | AbstractStage,
            /,
    ):
        for helper in self._result_repo_helpers:
            if isinstance(result_or_stage, AbstractStudentStageResult):
                if helper.is_acceptable_result_type(result_or_stage):
                    return helper
            elif isinstance(result_or_stage, AbstractStage):
                if helper.is_acceptable_stage(result_or_stage):
                    return helper
            else:
                assert False, type(result_or_stage)
        assert False, type(result_or_stage)

    def put(self, result: AbstractStudentStageResult) -> None:
        with self.__lock(result.student_id):
            helper = self._find_acceptable_repo_helper(result)
            helper.put(result)
            self._timestamp_repo_helper.update(result.student_id)

    def exists(self, student_id: StudentID, stage: AbstractStage) -> bool:
        with self.__lock(student_id):
            helper = self._find_acceptable_repo_helper(stage)
            return helper.exists(student_id, stage)

    def get(self, student_id: StudentID, stage: AbstractStage) -> AbstractStudentStageResult:
        with self.__lock(student_id):
            helper = self._find_acceptable_repo_helper(stage)
            return helper.get(student_id, stage)

    def delete(self, student_id: StudentID, stage: AbstractStage) -> None:
        with self.__lock(student_id):
            helper = self._find_acceptable_repo_helper(stage)
            helper.delete(student_id, stage)
            self._timestamp_repo_helper.update(student_id)

    def get_timestamp(self, student_id: StudentID) -> datetime | None:
        with self.__lock(student_id):
            return self._timestamp_repo_helper.get(student_id)

# # プロジェクト内ステートフル:
# #  - lru_cacheを保持するため
# #  - student_lock_serverを保持するため
# class StudentStageResultRepository:
#     def __init__(
#             self,
#             *,
#             student_stage_result_path_provider: StudentStageResultPathProvider,
#             current_project_core_io: CurrentProjectCoreIO,
#             lru_cache: LRUCache[tuple[StudentID, AbstractStage], AbstractStudentStageResult],
#     ):
#         self._student_stage_result_path_provider = student_stage_result_path_provider
#         self._current_project_core_io = current_project_core_io
#
#         self._student_lock_server = StudentLockServer()
#         self.__lru_cache = lru_cache
#
#     @contextmanager
#     def __lock(self, student_id: StudentID):
#         self._student_lock_server[student_id].lock()
#         try:
#             yield
#         finally:
#             self._student_lock_server[student_id].unlock()
#
#     @classmethod
#     def __get_type_name_of_result_type(
#             cls,
#             result_type: type[AbstractStudentStageResult],
#     ) -> str:
#         return result_type.__name__
#
#     RESULT_TYPES = (
#         BuildSuccessStudentStageResult,
#         BuildFailureStudentStageResult,
#         CompileSuccessStudentStageResult,
#         CompileFailureStudentStageResult,
#         ExecuteSuccessStudentStageResult,
#         ExecuteFailureStudentStageResult,
#         TestSuccessStudentStageResult,
#         TestFailureStudentStageResult,
#     )
#
#     @classmethod
#     def __get_result_type_from_type_name(
#             cls,
#             result_type_name: str,
#     ) -> type[AbstractStudentStageResult]:
#         for sub_cls in cls.RESULT_TYPES:
#             if result_type_name == cls.__get_type_name_of_result_type(sub_cls):
#                 return sub_cls
#         assert False, result_type_name
#
#     def put(
#             self,
#             result: AbstractStudentStageResult,
#     ) -> None:
#         with self.__lock(result.student_id):
#             json_fullpath = (
#                 self._student_stage_result_path_provider.result_json_fullpath(
#                     student_id=result.student_id,
#                     stage=result.stage,
#                 )
#             )
#             json_fullpath.parent.mkdir(parents=True, exist_ok=True)
#
#             self._current_project_core_io.write_json(
#                 json_fullpath=json_fullpath,
#                 body={
#                     "__type__": self.__get_type_name_of_result_type(type(result)),
#                     **result.to_json(),
#                 },
#             )
#             self.__lru_cache[(result.student_id, result.stage)] = result
#
#     def exists(
#             self,
#             student_id: StudentID,
#             stage: AbstractStage,
#     ) -> bool:
#         with self.__lock(student_id):
#             if (student_id, stage) in self.__lru_cache:
#                 return True
#
#             json_fullpath = (
#                 self._student_stage_result_path_provider.result_json_fullpath(
#                     student_id=student_id,
#                     stage=stage,
#                 )
#             )
#             return json_fullpath.exists()
#
#     def get(
#             self,
#             student_id: StudentID,
#             stage: AbstractStage,
#     ) -> AbstractStudentStageResult:
#         with self.__lock(student_id):
#             if (student_id, stage) in self.__lru_cache:
#                 return self.__lru_cache[(student_id, stage)]
#
#             json_fullpath = (
#                 self._student_stage_result_path_provider.result_json_fullpath(
#                     student_id=student_id,
#                     stage=stage,
#                 )
#             )
#             if not json_fullpath.exists():
#                 raise RepositoryItemNotFoundError(
#                     f"Build result for student {student_id} not found"
#                 )
#
#             body = self._current_project_core_io.read_json(json_fullpath=json_fullpath)
#             type_name = body.pop("__type__")
#             result_type = self.__get_result_type_from_type_name(type_name)
#             result = result_type.from_json(body)
#
#             self.__lru_cache[(student_id, stage)] = result
#
#             return result
#
#     def delete(
#             self,
#             student_id: StudentID,
#             stage: AbstractStage,
#     ) -> None:
#         with self.__lock(student_id):
#             if (student_id, stage) in self.__lru_cache:
#                 del self.__lru_cache[(student_id, stage)]
#
#             json_fullpath = (
#                 self._student_stage_result_path_provider.result_json_fullpath(
#                     student_id=student_id,
#                     stage=stage,
#                 )
#             )
#             if not json_fullpath.exists():
#                 raise RepositoryItemNotFoundError(
#                     f"Build result for student {student_id} not found"
#                 )
#
#             self._current_project_core_io.unlink(
#                 path=json_fullpath,
#             )
