import json

from autoprogen.domain.model.stage import AbstractStage, TestStage
from autoprogen.domain.model.student_stage_result import AbstractStudentStageResult, \
    TestSuccessStudentStageResult, TestFailureStudentStageResult
from autoprogen.domain.model.value import StudentID
from autoprogen.infra.repository.student_stage_path_result import _AbstractStageResultHelper


class _TestResultHelper(_AbstractStageResultHelper):
    """Test結果処理ヘルパー"""

    def create_table_if_not_exists(self, cursor) -> None:
        """TEST結果テーブルが存在しない場合に作成する。

        行が存在しない状態を未実行として扱う。正規な結果として扱う行は次の二種類とする。

        | 結果 | test_config_mtime | test_result_output_file_collection | error_group_id | error_type_id | error_params_json |
        | --- | --- | --- | --- | --- | --- |
        | 成功 | NOT NULL | NOT NULL | NULL | NULL | NULL |
        | 失敗 | NULL | NULL | NOT NULL | NOT NULL | NOT NULL |
        """
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS student_test_result
            (
                student_id                         TEXT,
                testcase_id                        TEXT,
                test_config_mtime                  DATETIME,
                test_result_output_file_collection TEXT,
                error_group_id                     TEXT,
                error_type_id                      TEXT,
                error_params_json                  TEXT,
                CHECK (
                    (error_group_id IS NULL AND error_type_id IS NULL AND error_params_json IS NULL)
                    OR
                    (error_group_id IS NOT NULL AND error_type_id IS NOT NULL AND error_params_json IS NOT NULL)
                ),
                PRIMARY KEY (student_id, testcase_id),
                FOREIGN KEY (student_id) REFERENCES student (student_id)
            )
            """
        )
        # TODO: column depending on json

    def get_stage_result(self, cursor, student_id: StudentID,
                         stage: AbstractStage) -> AbstractStudentStageResult | None:
        """TEST結果を取得し、構造化エラーを含むモデルへ復元する。"""
        assert isinstance(stage, TestStage), stage
        cursor.execute(
            "SELECT * FROM student_test_result WHERE student_id = ? AND testcase_id = ?",
            (str(student_id), str(stage.testcase_id))
        )
        row = cursor.fetchone()

        if row is None:
            return None

        error = self._decode_error(row)
        if error is None:
            from autoprogen.domain.model.student_stage_result import TestResultOutputFileCollection
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
                error=error,
            )

    def put_stage_result(self, cursor, result: AbstractStudentStageResult) -> None:
        """TESTの成功または失敗結果を保存する。"""
        if isinstance(result, TestSuccessStudentStageResult):
            cursor.execute(
                "INSERT OR REPLACE INTO student_test_result"
                "(student_id, testcase_id, test_config_mtime, test_result_output_file_collection, "
                "error_group_id, error_type_id, error_params_json)"
                "VALUES (?, ?, ?, ?, NULL, NULL, NULL)",
                (str(result.student_id), str(result.testcase_id),
                 result.test_config_mtime.isoformat(),
                 json.dumps(result.test_result_output_file_collection.to_json()))
            )
        elif isinstance(result, TestFailureStudentStageResult):
            encoded_error = self._encode_error(result.error)
            cursor.execute(
                "INSERT OR REPLACE INTO student_test_result"
                "(student_id, testcase_id, test_config_mtime, test_result_output_file_collection, "
                "error_group_id, error_type_id, error_params_json)"
                "VALUES (?, ?, NULL, NULL, ?, ?, ?)",
                (str(result.student_id), str(result.testcase_id), *encoded_error)
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
