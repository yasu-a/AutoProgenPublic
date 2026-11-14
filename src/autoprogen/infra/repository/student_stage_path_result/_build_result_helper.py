from autoprogen.domain.model.stage import AbstractStage, BuildStage
from autoprogen.domain.model.student_stage_result import AbstractStudentStageResult, \
    BuildSuccessStudentStageResult, BuildFailureStudentStageResult
from autoprogen.domain.model.value import StudentID
from autoprogen.infra.repository.student_stage_path_result import _AbstractStageResultHelper


class _BuildResultHelper(_AbstractStageResultHelper):
    """Build結果処理ヘルパー"""

    def create_table_if_not_exists(self, cursor) -> None:
        """BUILD結果テーブルが存在しない場合に作成する。

        行が存在しない状態を未実行として扱う。正規な結果として扱う行は次の二種類とする。

        | 結果 | submission_folder_checksum | error_group_id | error_type_id | error_params_json |
        | --- | --- | --- | --- | --- |
        | 成功 | NOT NULL | NULL | NULL | NULL |
        | 失敗 | NULL | NOT NULL | NOT NULL | NOT NULL |
        """
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS student_build_result
            (
                student_id                 TEXT PRIMARY KEY,
                submission_folder_checksum UNSIGNED INTEGER,
                error_group_id             TEXT,
                error_type_id              TEXT,
                error_params_json          TEXT,
                CHECK (
                    (error_group_id IS NULL AND error_type_id IS NULL AND error_params_json IS NULL)
                    OR
                    (error_group_id IS NOT NULL AND error_type_id IS NOT NULL AND error_params_json IS NOT NULL)
                ),
                FOREIGN KEY (student_id) REFERENCES student (student_id)
            )
            """
        )

    def get_stage_result(self, cursor, student_id: StudentID,
                         stage: AbstractStage) -> AbstractStudentStageResult | None:
        """BUILD結果を取得し、構造化エラーを含むモデルへ復元する。"""
        assert isinstance(stage, BuildStage), stage
        cursor.execute(
            "SELECT * FROM student_build_result WHERE student_id = ?",
            (str(student_id),)
        )
        row = cursor.fetchone()

        if row is None:
            return None

        error = self._decode_error(row)
        if error is None:
            return BuildSuccessStudentStageResult.create_instance(
                student_id=student_id,
                submission_folder_checksum=row["submission_folder_checksum"],
            )
        else:
            return BuildFailureStudentStageResult.create_instance(
                student_id=student_id,
                error=error,
            )

    def put_stage_result(self, cursor, result: AbstractStudentStageResult) -> None:
        """BUILDの成功または失敗結果を保存する。"""
        if isinstance(result, BuildSuccessStudentStageResult):
            cursor.execute(
                "INSERT OR REPLACE INTO student_build_result "
                "(student_id, submission_folder_checksum, error_group_id, error_type_id, error_params_json) "
                "VALUES (?, ?, NULL, NULL, NULL)",
                (str(result.student_id), result.submission_folder_checksum)
            )
        elif isinstance(result, BuildFailureStudentStageResult):
            encoded_error = self._encode_error(result.error)
            cursor.execute(
                "INSERT OR REPLACE INTO student_build_result "
                "(student_id, submission_folder_checksum, error_group_id, error_type_id, error_params_json) "
                "VALUES (?, NULL, ?, ?, ?)",
                (str(result.student_id), *encoded_error)
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
