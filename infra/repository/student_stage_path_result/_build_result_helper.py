from domain.model.stage import AbstractStage, BuildStage
from domain.model.student_stage_result import AbstractStudentStageResult, \
    BuildSuccessStudentStageResult, BuildFailureStudentStageResult
from domain.model.value import StudentID
from infra.repository.student_stage_path_result import _AbstractStageResultHelper


class _BuildResultHelper(_AbstractStageResultHelper):
    """Build結果処理ヘルパー"""

    def create_table_if_not_exists(self, cursor) -> None:
        cursor.execute(
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

    def get_stage_result(self, cursor, student_id: StudentID,
                         stage: AbstractStage) -> AbstractStudentStageResult | None:
        assert isinstance(stage, BuildStage), stage
        cursor.execute(
            "SELECT * FROM student_build_result WHERE student_id = ?",
            (str(student_id),)
        )
        row = cursor.fetchone()

        if row is None:
            return None

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

    def put_stage_result(self, cursor, result: AbstractStudentStageResult) -> None:
        if isinstance(result, BuildSuccessStudentStageResult):
            cursor.execute(
                "INSERT OR REPLACE INTO student_build_result "
                "(student_id, submission_folder_checksum, reason) "
                "VALUES (?, ?, NULL)",
                (str(result.student_id), result.submission_folder_checksum)
            )
        elif isinstance(result, BuildFailureStudentStageResult):
            cursor.execute(
                "INSERT OR REPLACE INTO student_build_result "
                "(student_id, submission_folder_checksum, reason) "
                "VALUES (?, NULL, ?)",
                (str(result.student_id), result.reason)
            )
        else:
            raise ValueError(f"Unexpected result type: {type(result)}")

    def delete_stage_result(self, cursor, student_id: StudentID, stage: AbstractStage) -> None:
        assert isinstance(stage, BuildStage), stage
        cursor.execute(
            "DELETE FROM student_build_result WHERE student_id = ?",
            (str(student_id),)
        )

    def exists_stage_result(self, cursor, student_id: StudentID, stage: AbstractStage) -> bool:
        assert isinstance(stage, BuildStage), stage
        cursor.execute(
            "SELECT EXISTS(SELECT 1 FROM student_build_result WHERE student_id = ?)",
            (str(student_id),)
        )
        return bool(cursor.fetchone()[0])
