import json

from domain.model.stage import AbstractStage, TestStage
from domain.model.student_stage_result import AbstractStudentStageResult, \
    TestSuccessStudentStageResult, TestFailureStudentStageResult
from domain.model.value import StudentID
from infra.repository.student_stage_path_result import _AbstractStageResultHelper


class _TestResultHelper(_AbstractStageResultHelper):
    """Test結果処理ヘルパー"""

    def create_table_if_not_exists(self, cursor) -> None:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS student_test_result
            (
                student_id                         TEXT,
                testcase_id                        TEXT,
                test_config_mtime                  DATETIME,
                test_result_output_file_collection TEXT,
                reason                             TEXT,
                PRIMARY KEY (student_id, testcase_id),
                FOREIGN KEY (student_id) REFERENCES student (student_id)
            )
            """
        )
        # TODO: column depending on json

    def get_stage_result(self, cursor, student_id: StudentID,
                         stage: AbstractStage) -> AbstractStudentStageResult | None:
        assert isinstance(stage, TestStage), stage
        cursor.execute(
            "SELECT * FROM student_test_result WHERE student_id = ? AND testcase_id = ?",
            (str(student_id), str(stage.testcase_id))
        )
        row = cursor.fetchone()

        if row is None:
            return None

        if row["reason"] is None:
            from domain.model.student_stage_result import TestResultOutputFileCollection
            test_result_output_file_collection = TestResultOutputFileCollection.from_json(
                json.loads(row["test_result_output_file_collection"])
            )
            return TestSuccessStudentStageResult.create_instance(
                student_id=student_id,
                testcase_id=stage.testcase_id,
                test_config_mtime=row["test_config_mtime"],  # 既にdatetimeオブジェクト
                test_result_output_file_collection=test_result_output_file_collection,
            )
        else:
            return TestFailureStudentStageResult.create_instance(
                student_id=student_id,
                testcase_id=stage.testcase_id,
                reason=row["reason"],
            )

    def put_stage_result(self, cursor, result: AbstractStudentStageResult) -> None:
        if isinstance(result, TestSuccessStudentStageResult):
            cursor.execute(
                "INSERT OR REPLACE INTO student_test_result"
                "(student_id, testcase_id, test_config_mtime, test_result_output_file_collection, reason)"
                "VALUES (?, ?, ?, ?, NULL)",
                (str(result.student_id), str(result.testcase_id),
                 result.test_config_mtime.isoformat(),
                 json.dumps(result.test_result_output_file_collection.to_json()))
            )
        elif isinstance(result, TestFailureStudentStageResult):
            cursor.execute(
                "INSERT OR REPLACE INTO student_test_result"
                "(student_id, testcase_id, test_config_mtime, test_result_output_file_collection, reason)"
                "VALUES (?, ?, NULL, NULL, ?)",
                (str(result.student_id), str(result.testcase_id), result.reason)
            )
        else:
            raise ValueError(f"Unexpected result type: {type(result)}")

    def delete_stage_result(self, cursor, student_id: StudentID, stage: AbstractStage) -> None:
        assert isinstance(stage, TestStage), stage
        cursor.execute(
            "DELETE FROM student_test_result WHERE student_id = ? AND testcase_id = ?",
            (str(student_id), str(stage.testcase_id))
        )

    def exists_stage_result(self, cursor, student_id: StudentID, stage: AbstractStage) -> bool:
        assert isinstance(stage, TestStage), stage
        cursor.execute(
            "SELECT EXISTS(SELECT 1 FROM student_test_result WHERE student_id = ? AND testcase_id = ?)",
            (str(student_id), str(stage.testcase_id))
        )
        return bool(cursor.fetchone()[0])
