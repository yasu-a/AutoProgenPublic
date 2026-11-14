import json

from autoprogen.domain.model.stage import AbstractStage, CompileStage
from autoprogen.domain.model.student_stage_result import AbstractStudentStageResult, \
    CompileSuccessStudentStageResult, CompileFailureStudentStageResult, SourceCodeCheckPolicy
from autoprogen.domain.model.value import StudentID
from autoprogen.infra.repository.student_stage_path_result import _AbstractStageResultHelper


class _CompileResultHelper(_AbstractStageResultHelper):
    """Compile結果処理ヘルパー"""

    def create_table_if_not_exists(self, cursor) -> None:
        """COMPILE結果テーブルが存在しない場合に作成する。

        行が存在しない状態を未実行として扱う。outputは成功・失敗の両方で保持する。
        正規な結果として扱う行は次の二種類とする。

        | 結果 | output | error_group_id | error_type_id | error_params_json | security_check_policy_json | security_check_skipped |
        | --- | --- | --- | --- | --- | --- | --- |
        | 成功 | NOT NULL | NULL | NULL | NULL | NOT NULL | NOT NULL |
        | 失敗 | NOT NULL | NOT NULL | NOT NULL | NOT NULL | NULL | NULL |
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
                security_check_policy_json TEXT,
                security_check_skipped INTEGER,
                CHECK (
                    (
                        error_group_id IS NULL
                        AND error_type_id IS NULL
                        AND error_params_json IS NULL
                        AND security_check_policy_json IS NOT NULL
                        AND security_check_skipped IS NOT NULL
                    )
                    OR
                    (
                        error_group_id IS NOT NULL
                        AND error_type_id IS NOT NULL
                        AND error_params_json IS NOT NULL
                        AND security_check_policy_json IS NULL
                        AND security_check_skipped IS NULL
                    )
                ),
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
        if error is None:
            policy_json = json.loads(row["security_check_policy_json"])
            if row["security_check_skipped"] not in (0, 1):
                raise ValueError("security_check_skippedは0または1である必要があります")
            return CompileSuccessStudentStageResult.create_instance(
                student_id=student_id,
                output=row["output"],
                security_check_policy=SourceCodeCheckPolicy.from_json(policy_json),
                security_check_skipped=bool(row["security_check_skipped"]),
            )
        else:
            return CompileFailureStudentStageResult.create_instance(
                student_id=student_id,
                error=error,
                output=row["output"],
            )

    def put_stage_result(self, cursor, result: AbstractStudentStageResult) -> None:
        """COMPILEの成功または失敗結果を保存する。"""
        if isinstance(result, CompileSuccessStudentStageResult):
            cursor.execute(
                "INSERT OR REPLACE INTO student_compile_result "
                "(student_id, output, error_group_id, error_type_id, error_params_json, "
                "security_check_policy_json, security_check_skipped) "
                "VALUES (?, ?, NULL, NULL, NULL, ?, ?)",
                (
                    str(result.student_id),
                    result.output,
                    json.dumps(
                        result.security_check_policy.to_json(),
                        ensure_ascii=False,
                    ),
                    int(result.security_check_skipped),
                )
            )
        elif isinstance(result, CompileFailureStudentStageResult):
            encoded_error = self._encode_error(result.error)
            cursor.execute(
                "INSERT OR REPLACE INTO student_compile_result "
                "(student_id, output, error_group_id, error_type_id, error_params_json, "
                "security_check_policy_json, security_check_skipped) "
                "VALUES (?, ?, ?, ?, ?, NULL, NULL)",
                (str(result.student_id), result.output, *encoded_error)
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
