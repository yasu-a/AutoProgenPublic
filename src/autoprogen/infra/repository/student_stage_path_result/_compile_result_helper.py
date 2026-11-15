import json

from autoprogen.domain.model.stage import AbstractStage, CompileStage
from autoprogen.domain.model.project_settings import SourceCodeCheckSuppressions
from autoprogen.domain.model.student_stage_result import AbstractStudentStageResult, \
    CompileStudentStageResult
from autoprogen.domain.model.value import StudentID
from autoprogen.infra.repository.student_stage_path_result import _AbstractStageResultHelper


class _CompileResultHelper(_AbstractStageResultHelper):
    """Compile結果処理ヘルパー"""

    def create_table_if_not_exists(self, cursor) -> None:
        """COMPILE結果テーブルが存在しない場合に作成する。

        行が存在しない状態を未実行として扱う。outputは成功・失敗の両方で保持する。
        正規な結果として扱う行は次の二種類とする。

        | 結果 | output | error_group_id | error_type_id | error_params_json | suppressed_source_code_checks_json | source_code_check_skipped |
        | --- | --- | --- | --- | --- | --- | --- |
        | 成功 | NOT NULL | NULL | NULL | NULL | NOT NULL | NOT NULL |
        | 失敗 | NOT NULL | NOT NULL | NOT NULL | NOT NULL | NOT NULL | NOT NULL |
        """
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS student_compile_result
            (
                student_id TEXT PRIMARY KEY,
                output     TEXT NOT NULL,
                error_group_id TEXT,
                error_type_id TEXT,
                error_params_json TEXT,
                suppressed_source_code_checks_json TEXT NOT NULL,
                source_code_check_skipped INTEGER NOT NULL,
                CHECK (
                    (
                        error_group_id IS NULL
                        AND error_type_id IS NULL
                        AND error_params_json IS NULL
                    )
                    OR
                    (
                        error_group_id IS NOT NULL
                        AND error_type_id IS NOT NULL
                        AND error_params_json IS NOT NULL
                    )
                ),
                CHECK (source_code_check_skipped IN (0, 1)),
                FOREIGN KEY (student_id) REFERENCES student (student_id)
            )
            """
        )

    def get_stage_result(self, cursor, student_id: StudentID,
                         stage: AbstractStage) -> AbstractStudentStageResult | None:
        """COMPILE結果と実行時の安全性チェック状態を復元する。"""
        assert isinstance(stage, CompileStage), stage
        cursor.execute(
            "SELECT * FROM student_compile_result WHERE student_id = ?",
            (str(student_id),)
        )
        row = cursor.fetchone()

        if row is None:
            return None

        error = self._decode_error(row)
        suppressions_json = json.loads(row["suppressed_source_code_checks_json"])
        return CompileStudentStageResult.create_instance(
            student_id=student_id,
            output=row["output"],
            suppressed_source_code_checks=SourceCodeCheckSuppressions.from_json(
                suppressions_json,
            ),
            source_code_check_skipped=bool(row["source_code_check_skipped"]),
            error=error,
        )

    def put_stage_result(self, cursor, result: AbstractStudentStageResult) -> None:
        """COMPILEの成功または失敗結果を保存する。"""
        if isinstance(result, CompileStudentStageResult):
            if result.error is None:
                encoded_error = (None, None, None)
            else:
                encoded_error = self._encode_error(result.error)
            cursor.execute(
                "INSERT OR REPLACE INTO student_compile_result "
                "(student_id, output, error_group_id, error_type_id, error_params_json, "
                "suppressed_source_code_checks_json, source_code_check_skipped) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    str(result.student_id),
                    result.output,
                    *encoded_error,
                    json.dumps(
                        result.suppressed_source_code_checks.to_json(),
                        ensure_ascii=False,
                    ),
                    int(result.source_code_check_skipped),
                )
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
