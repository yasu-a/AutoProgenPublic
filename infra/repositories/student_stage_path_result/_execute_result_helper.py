import json
from datetime import datetime

from domain.models.stages import AbstractStage, ExecuteStage
from domain.models.student_stage_result import AbstractStudentStageResult, \
    ExecuteSuccessStudentStageResult, ExecuteFailureStudentStageResult
from domain.models.values import StudentID
from infra.repositories.student_stage_path_result import _AbstractStageResultHelper


class _ExecuteResultHelper(_AbstractStageResultHelper):
    """Execute結果処理ヘルパー"""

    def create_table_if_not_exists(self, cursor) -> None:
        cursor.execute(
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
        # TODO: column depending on json

    def get_stage_result(self, cursor, student_id: StudentID,
                         stage: AbstractStage) -> AbstractStudentStageResult | None:
        assert isinstance(stage, ExecuteStage), stage
        cursor.execute(
            "SELECT * FROM student_execute_result WHERE student_id = ? AND testcase_id = ?",
            (str(student_id), str(stage.testcase_id))
        )
        row = cursor.fetchone()

        if row is None:
            return None

        if row["reason"] is None:
            from domain.models.output_file import OutputFileMapping
            output_files = OutputFileMapping.from_json(json.loads(row["output_files_json"]))
            return ExecuteSuccessStudentStageResult.create_instance(
                student_id=student_id,
                testcase_id=stage.testcase_id,
                execute_config_mtime=datetime.fromisoformat(row["execute_config_mtime"]),
                output_files=output_files,
            )
        else:
            return ExecuteFailureStudentStageResult.create_instance(
                student_id=student_id,
                testcase_id=stage.testcase_id,
                reason=row["reason"],
            )

    def put_stage_result(self, cursor, result: AbstractStudentStageResult) -> None:
        if isinstance(result, ExecuteSuccessStudentStageResult):
            cursor.execute(
                "INSERT OR REPLACE INTO student_execute_result (student_id, testcase_id, execute_config_mtime, output_files_json, reason) VALUES (?, ?, ?, ?, NULL)",
                (str(result.student_id), str(result.testcase_id),
                 result.execute_config_mtime.isoformat(), json.dumps(result.output_files.to_json()))
            )
        elif isinstance(result, ExecuteFailureStudentStageResult):
            cursor.execute(
                "INSERT OR REPLACE INTO student_execute_result (student_id, testcase_id, execute_config_mtime, output_files_json, reason) VALUES (?, ?, NULL, NULL, ?)",
                (str(result.student_id), str(result.testcase_id), result.reason)
            )
        else:
            raise ValueError(f"Unexpected result type: {type(result)}")

    def delete_stage_result(self, cursor, student_id: StudentID, stage: AbstractStage) -> None:
        assert isinstance(stage, ExecuteStage), stage
        cursor.execute(
            "DELETE FROM student_execute_result WHERE student_id = ? AND testcase_id = ?",
            (str(student_id), str(stage.testcase_id))
        )

    def exists_stage_result(self, cursor, student_id: StudentID, stage: AbstractStage) -> bool:
        assert isinstance(stage, ExecuteStage), stage
        cursor.execute(
            "SELECT EXISTS(SELECT 1 FROM student_execute_result WHERE student_id = ? AND testcase_id = ?)",
            (str(student_id), str(stage.testcase_id))
        )
        return bool(cursor.fetchone()[0])
