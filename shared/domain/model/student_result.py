from datetime import datetime
from enum import Enum, auto

from shared.domain.model.stage import Stage
from shared.domain.value.identifier import StudentID, TestCaseID
from shared.domain.value.output_file import OutputFileCollection
from shared.domain.value.student_stage_result import TestResultOutputFileCollection


class StudentStageStatusFlag(Enum):
    """学生ステージ状態セルデータの状態を表すEnum"""
    UNFINISHED = auto()
    FINISHED_SUCCESS = auto()
    FINISHED_FAILURE = auto()


class StudentStageStatusEntity:
    def __init__(
            self,
            student_id: StudentID,
            build_status: StudentStageStatusFlag,
            compile_status: StudentStageStatusFlag,
            execute_status: dict[TestCaseID, StudentStageStatusFlag],
            test_status: dict[TestCaseID, StudentStageStatusFlag],
            timestamp: datetime | None = None,
    ):
        self._student_id = student_id
        self.build_status = build_status
        self.compile_status = compile_status
        self.execute_status = execute_status
        self.test_status = test_status
        self.timestamp = timestamp

        self._validate()

    def _validate(self):
        # 1. 単純なフィールドの型チェック
        if not isinstance(self._student_id, StudentID):
            raise TypeError(
                f"student_id must be an instance of StudentID, not {type(self._student_id).__name__}"
            )

        if not isinstance(self.build_status, StudentStageStatusFlag):
            raise TypeError(
                f"build_status must be an instance of StudentStageStatusFlag, not {type(self.build_status).__name__}"
            )

        if not isinstance(self.compile_status, StudentStageStatusFlag):
            raise TypeError(
                f"compile_status must be an instance of StudentStageStatusFlag, not {type(self.compile_status).__name__}"
            )

        # 2. 辞書フィールドの型チェック (コンテナ型 + 中身の型)
        self._validate_dict_contents(
            target_dict=self.execute_status,
            expected_key_type=TestCaseID,
            expected_value_type=StudentStageStatusFlag,
            field_name="execute_status"
        )

        self._validate_dict_contents(
            target_dict=self.test_status,
            expected_key_type=TestCaseID,
            expected_value_type=StudentStageStatusFlag,
            field_name="test_status"
        )

    def _validate_dict_contents(
            self,
            target_dict: dict,
            expected_key_type: type,
            expected_value_type: type,
            field_name: str
    ):
        """辞書自身と、その中身（Key/Value）の型を検証するヘルパー"""

        # コンテナ自体のチェック
        if not isinstance(target_dict, dict):
            raise TypeError(
                f"{field_name} must be a dict, not {type(target_dict).__name__}"
            )

        # 中身のチェック
        for key, value in target_dict.items():
            if not isinstance(key, expected_key_type):
                raise TypeError(
                    f"Key in {field_name} must be {expected_key_type.__name__}, "
                    f"found {type(key).__name__} (Key: {key})"
                )
            if not isinstance(value, expected_value_type):
                raise TypeError(
                    f"Value in {field_name} must be {expected_value_type.__name__}, "
                    f"found {type(value).__name__} (Value for key {key}: {value})"
                )


class StudentStageResultEntity:
    def __init__(
            self,
            student_id: StudentID,
            stage: Stage,
            testcase_id: TestCaseID | None,
            output: str | None,
            error_message: str | None,
            timestamp: datetime,
    ):
        self._student_id = student_id
        self._stage = stage
        self._testcase_id = testcase_id

        self._output = output
        self._error_message = error_message
        self._timestamp = timestamp

        self._validate()

    def _validate(self):
        if self._stage.is_testcase_required():
            if not isinstance(self._testcase_id, TestCaseID):
                raise TypeError(
                    f"result of stage {self._stage!s} must be initialized with testcase_id"
                )
        else:
            if self._testcase_id is not None:
                raise TypeError(
                    f"result of stage {self._stage!s} must be initialized without testcase_id"
                )


class AbstractStageResultEntity:
    """軽量なリポジトリ用エンティティ基底クラス"""

    def __init__(
            self,
            student_id: StudentID,
            stage: Stage,
            testcase_id: TestCaseID | None,
            is_success: bool,
            timestamp: datetime,
            error_summary: str | None = None,
    ):
        self._student_id = student_id
        self._stage = stage
        self._testcase_id = testcase_id
        self.is_success = is_success
        self.timestamp = timestamp
        self.error_summary = error_summary

        self._validate()

    @property
    def student_id(self) -> StudentID:
        return self._student_id

    @property
    def stage(self) -> Stage:
        return self._stage

    @property
    def testcase_id(self) -> TestCaseID | None:
        return self._testcase_id

    def _validate(self):
        if self._stage.is_testcase_required():
            if not isinstance(self._testcase_id, TestCaseID):
                raise TypeError(
                    f"result of stage {self._stage!s} must be initialized with testcase_id"
                )
        else:
            if self._testcase_id is not None:
                raise TypeError(
                    f"result of stage {self._stage!s} must be initialized without testcase_id"
                )


class BuildStageResultEntity(AbstractStageResultEntity):
    def __init__(
            self,
            *,
            student_id: StudentID,
            submission_folder_checksum: int | None,
            timestamp: datetime,
            is_success: bool,
            error_summary: str | None = None,
    ):
        super().__init__(
            student_id=student_id,
            stage=Stage.BUILD,
            testcase_id=None,
            is_success=is_success,
            timestamp=timestamp,
            error_summary=error_summary,
        )
        self.submission_folder_checksum = submission_folder_checksum


class CompileStageResultEntity(AbstractStageResultEntity):
    def __init__(
            self,
            *,
            student_id: StudentID,
            output: str | None,
            timestamp: datetime,
            is_success: bool,
            error_summary: str | None = None,
    ):
        super().__init__(
            student_id=student_id,
            stage=Stage.COMPILE,
            testcase_id=None,
            is_success=is_success,
            timestamp=timestamp,
            error_summary=error_summary,
        )
        self.output = output


class ExecuteStageResultEntity(AbstractStageResultEntity):
    def __init__(
            self,
            *,
            student_id: StudentID,
            testcase_id: TestCaseID,
            execute_config_mtime: datetime | None,
            output_file_collection: OutputFileCollection | None,
            timestamp: datetime,
            is_success: bool,
            error_summary: str | None = None,
    ):
        super().__init__(
            student_id=student_id,
            stage=Stage.EXECUTE,
            testcase_id=testcase_id,
            is_success=is_success,
            timestamp=timestamp,
            error_summary=error_summary,
        )
        self.execute_config_mtime = execute_config_mtime
        self.output_file_collection = output_file_collection


class TestStageResultEntity(AbstractStageResultEntity):
    def __init__(
            self,
            *,
            student_id: StudentID,
            testcase_id: TestCaseID,
            test_config_mtime: datetime | None,
            test_result_output_file_collection: TestResultOutputFileCollection | None,
            failure_reason: str | None,
            timestamp: datetime,
            is_success: bool,
            error_summary: str | None = None,
    ):
        super().__init__(
            student_id=student_id,
            stage=Stage.TEST,
            testcase_id=testcase_id,
            is_success=is_success,
            timestamp=timestamp,
            error_summary=error_summary,
        )
        self.test_config_mtime = test_config_mtime
        self.test_result_output_file_collection = test_result_output_file_collection
        self.failure_reason = failure_reason

    @property
    def is_accepted(self) -> bool:
        """テストケースが正解かどうか"""
        if self.test_result_output_file_collection is None:
            return False
        return self.test_result_output_file_collection.is_accepted
