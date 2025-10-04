from domain.model.stage import AbstractStage, CompileStage
from domain.model.student_stage_result import AbstractStudentStageResult, \
    CompileSuccessStudentStageResult, CompileFailureStudentStageResult
from domain.model.value import StudentID
from infra.repository.student_stage_path_result import _AbstractStageResultHelper


class _CompileResultHelper(_AbstractStageResultHelper):
    """Compile結果処理ヘルパー"""

    def create_table_if_not_exists(self, cursor) -> None:
        cursor.execute(
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

    def get_stage_result(self, cursor, student_id: StudentID,
                         stage: AbstractStage) -> AbstractStudentStageResult | None:
        assert isinstance(stage, CompileStage), stage
        cursor.execute(
            "SELECT * FROM student_compile_result WHERE student_id = ?",
            (str(student_id),)
        )
        row = cursor.fetchone()

        if row is None:
            return None

        if row["reason"] is None:
            return CompileSuccessStudentStageResult.create_instance(
                student_id=student_id,
                output=row["output"],
            )
        else:
            return CompileFailureStudentStageResult.create_instance(
                student_id=student_id,
                reason=row["reason"],
                output=row["output"],
            )

    def put_stage_result(self, cursor, result: AbstractStudentStageResult) -> None:
        if isinstance(result, CompileSuccessStudentStageResult):
            cursor.execute(
                "INSERT OR REPLACE INTO student_compile_result (student_id, output, reason) VALUES (?, ?, NULL)",
                (str(result.student_id), result.output)
            )
        elif isinstance(result, CompileFailureStudentStageResult):
            cursor.execute(
                "INSERT OR REPLACE INTO student_compile_result (student_id, output, reason) VALUES (?, ?, ?)",
                (str(result.student_id), result.output, result.reason)
            )
        else:
            raise ValueError(f"Unexpected result type: {type(result)}")

    def delete_stage_result(self, cursor, student_id: StudentID, stage: AbstractStage) -> None:
        assert isinstance(stage, CompileStage), stage
        cursor.execute(
            "DELETE FROM student_compile_result WHERE student_id = ?",
            (str(student_id),)
        )

    def exists_stage_result(self, cursor, student_id: StudentID, stage: AbstractStage) -> bool:
        assert isinstance(stage, CompileStage), stage
        cursor.execute(
            "SELECT EXISTS(SELECT 1 FROM student_compile_result WHERE student_id = ?)",
            (str(student_id),)
        )
        return bool(cursor.fetchone()[0])
