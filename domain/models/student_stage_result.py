from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import TypeVar

from domain.models.output_file import OutputFileMapping
from domain.models.stages import AbstractStage, BuildStage, CompileStage, ExecuteStage, TestStage
from domain.models.test_result_output_file_entry import AbstractTestResultOutputFileEntry
from domain.models.values import FileID, StudentID, TestCaseID


@dataclass(slots=True)
class AbstractStudentStageResult(ABC):  # 各ステージの結果の基底クラス
    student_id: StudentID
    stage: AbstractStage

    @property
    @abstractmethod
    def is_success(self) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def to_json(self):
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def from_json(cls, body):
        raise NotImplementedError()


@dataclass(slots=True)
class AbstractSuccessStudentStageResult(AbstractStudentStageResult, ABC):
    @property
    def is_success(self) -> bool:
        return True


@dataclass(slots=True)
class AbstractFailureStudentStageResult(AbstractStudentStageResult, ABC):
    reason: str

    @property
    def is_success(self) -> bool:
        return False

    @property
    def detailed_text(self) -> str | None:
        return "（エラーメッセージが設定なし）"


@dataclass(slots=True)
class BuildSuccessStudentStageResult(AbstractSuccessStudentStageResult):  # 生徒ごと
    submission_folder_checksum: int

    def __post_init__(self):
        assert isinstance(self.stage, BuildStage)

    @classmethod
    def create_instance(cls, *, student_id: StudentID, submission_folder_checksum: int):
        return cls(
            student_id=student_id,
            stage=BuildStage(),
            submission_folder_checksum=submission_folder_checksum,
        )

    def to_json(self):
        return {
            "student_id": self.student_id.to_json(),
            "stage": self.stage.to_json(),
            "submission_folder_hash": self.submission_folder_checksum,
        }

    @classmethod
    def from_json(cls, body):
        return cls(
            student_id=StudentID.from_json(body["student_id"]),
            stage=AbstractStage.from_json(body["stage"]),
            submission_folder_checksum=body["submission_folder_hash"],
        )


@dataclass(slots=True)
class BuildFailureStudentStageResult(AbstractFailureStudentStageResult):  # 生徒ごと
    def __post_init__(self):
        assert isinstance(self.stage, BuildStage)

    @classmethod
    def create_instance(cls, *, student_id: StudentID, reason: str):
        return cls(
            student_id=student_id,
            stage=BuildStage(),
            reason=reason,
        )

    def to_json(self):
        return {
            "student_id": self.student_id.to_json(),
            "stage": self.stage.to_json(),
            "reason": self.reason,
        }

    @classmethod
    def from_json(cls, body):
        return cls(
            student_id=StudentID.from_json(body["student_id"]),
            stage=AbstractStage.from_json(body["stage"]),
            reason=body["reason"],
        )

    @property
    def detailed_text(self) -> str | None:
        return self.reason


BuildStageResultType = TypeVar(
    "BuildStageResultType",
    bound=BuildSuccessStudentStageResult | BuildFailureStudentStageResult,
)


@dataclass(slots=True)
class CompileSuccessStudentStageResult(AbstractSuccessStudentStageResult):  # 生徒ごと
    output: str

    def __post_init__(self):
        assert isinstance(self.stage, CompileStage)

    @classmethod
    def create_instance(cls, *, student_id: StudentID, output: str):
        return cls(
            student_id=student_id,
            stage=CompileStage(),
            output=output,
        )

    def to_json(self):
        return {
            "student_id": self.student_id.to_json(),
            "stage": self.stage.to_json(),
            "output": self.output,
        }

    @classmethod
    def from_json(cls, body):
        return cls(
            student_id=StudentID.from_json(body["student_id"]),
            stage=AbstractStage.from_json(body["stage"]),
            output=body["output"],
        )


@dataclass(slots=True)
class CompileFailureStudentStageResult(AbstractFailureStudentStageResult):  # 生徒ごと
    output: str

    def __post_init__(self):
        assert isinstance(self.stage, CompileStage)

    @classmethod
    def create_instance(cls, *, student_id: StudentID, reason: str, output: str):
        return cls(
            student_id=student_id,
            stage=CompileStage(),
            reason=reason,
            output=output,
        )

    def to_json(self):
        return {
            "student_id": self.student_id.to_json(),
            "stage": self.stage.to_json(),
            "reason": self.reason,
            "output": self.output,
        }

    @classmethod
    def from_json(cls, body):
        return cls(
            student_id=StudentID.from_json(body["student_id"]),
            stage=AbstractStage.from_json(body["stage"]),
            reason=body["reason"],
            output=body["output"],
        )

    @property
    def detailed_text(self) -> str | None:
        return self.reason + "\n" + self.output


CompileStageResultType = TypeVar(
    "CompileStageResultType",
    bound=CompileSuccessStudentStageResult | CompileFailureStudentStageResult,
)


@dataclass(slots=True)
class ExecuteSuccessStudentStageResult(AbstractSuccessStudentStageResult):  # 生徒・テストケースごと
    execute_config_mtime: datetime
    output_files: OutputFileMapping

    def __post_init__(self):
        assert isinstance(self.stage, ExecuteStage)

    @classmethod
    def create_instance(
            cls,
            *,
            student_id: StudentID,
            testcase_id: TestCaseID,
            execute_config_mtime: datetime,
            output_files: OutputFileMapping,
    ):
        return cls(
            student_id=student_id,
            stage=ExecuteStage(testcase_id=testcase_id),
            execute_config_mtime=execute_config_mtime,
            output_files=output_files,
        )

    def to_json(self):
        return {
            "student_id": self.student_id.to_json(),
            "stage": self.stage.to_json(),
            "execute_config_mtime": self.execute_config_mtime.isoformat(),
            "output_files": self.output_files.to_json(),
        }

    @classmethod
    def from_json(cls, body):
        return cls(
            student_id=StudentID.from_json(body["student_id"]),
            stage=AbstractStage.from_json(body["stage"]),
            execute_config_mtime=datetime.fromisoformat(body["execute_config_mtime"]),
            output_files=OutputFileMapping.from_json(body["output_files"]),
        )


@dataclass(slots=True)
class ExecuteFailureStudentStageResult(AbstractFailureStudentStageResult):  # 生徒・テストケースごと
    def __post_init__(self):
        assert isinstance(self.stage, ExecuteStage)

    @classmethod
    def create_instance(
            cls,
            *,
            student_id: StudentID,
            testcase_id: TestCaseID,
            reason: str,
    ):
        return cls(
            student_id=student_id,
            stage=ExecuteStage(testcase_id=testcase_id),
            reason=reason,
        )

    def to_json(self) -> dict:
        return {
            "student_id": self.student_id.to_json(),
            "stage": self.stage.to_json(),
            "reason": self.reason,
        }

    @classmethod
    def from_json(cls, body: dict):
        return cls(
            student_id=StudentID.from_json(body["student_id"]),
            stage=AbstractStage.from_json(body["stage"]),
            reason=body["reason"],
        )

    @property
    def detailed_text(self) -> str | None:
        return self.reason


ExecuteStageResultType = TypeVar(
    "ExecuteStageResultType",
    bound=ExecuteSuccessStudentStageResult | ExecuteFailureStudentStageResult,
)


class TestResultOutputFileMapping(
    dict[FileID, AbstractTestResultOutputFileEntry],
):
    def to_json(self) -> dict[str, dict]:
        return {
            file_id.to_json(): result.to_json()
            for file_id, result in self.items()
        }

    @classmethod
    def from_json(cls, body: dict) -> "TestResultOutputFileMapping":
        return cls({
            FileID.from_json(file_id_str): AbstractTestResultOutputFileEntry.from_json(result_body)
            for file_id_str, result_body in body.items()
        })

    @property
    def is_accepted(self) -> bool:  # テストケースが正解かどうか
        for file_id, file_entry in self.items():
            # 実行結果の出力がない
            if file_entry.has_expected and not file_entry.has_actual:
                return False
            # 予期されていない実行結果
            if not file_entry.has_expected and file_entry.has_actual:
                continue
            # 不正解
            if not file_entry.test_result.is_accepted:
                return False
        return True


@dataclass(slots=True)
class TestSuccessStudentStageResult(AbstractSuccessStudentStageResult):  # 生徒・テストケースごと
    test_config_mtime: datetime
    test_result_output_files: TestResultOutputFileMapping

    def __post_init__(self):
        assert isinstance(self.stage, TestStage)

    @classmethod
    def create_instance(
            cls,
            *,
            student_id: StudentID,
            testcase_id: TestCaseID,
            test_config_mtime: datetime,
            test_result_output_files: TestResultOutputFileMapping,
    ):
        return cls(
            student_id=student_id,
            stage=TestStage(testcase_id=testcase_id),
            test_config_mtime=test_config_mtime,
            test_result_output_files=test_result_output_files,
        )

    def to_json(self) -> dict:
        return {
            "student_id": self.student_id.to_json(),
            "stage": self.stage.to_json(),
            "test_config_mtime": self.test_config_mtime.isoformat(),
            "test_result_output_files": self.test_result_output_files.to_json(),
        }

    @classmethod
    def from_json(cls, body: dict) -> "TestSuccessStudentStageResult":
        return cls(
            student_id=StudentID.from_json(body["student_id"]),
            stage=AbstractStage.from_json(body["stage"]),
            test_config_mtime=datetime.fromisoformat(body["test_config_mtime"]),
            test_result_output_files=TestResultOutputFileMapping.from_json(
                body["test_result_output_files"],
            ),
        )


@dataclass(slots=True)
class TestFailureStudentStageResult(AbstractFailureStudentStageResult):  # 生徒・テストケースごと
    def __post_init__(self):
        assert isinstance(self.stage, TestStage), self.stage

    @classmethod
    def create_instance(
            cls,
            *,
            student_id: StudentID,
            testcase_id: TestCaseID,
            reason: str,
    ):
        return cls(
            student_id=student_id,
            stage=TestStage(testcase_id=testcase_id),
            reason=reason,
        )

    def to_json(self) -> dict:
        return {
            "student_id": self.student_id.to_json(),
            "stage": self.stage.to_json(),
            "reason": self.reason,
        }

    @classmethod
    def from_json(cls, body: dict) -> "TestFailureStudentStageResult":
        return cls(
            student_id=StudentID.from_json(body["student_id"]),
            stage=AbstractStage.from_json(body["stage"]),
            reason=body["reason"],
        )

    @property
    def detailed_text(self) -> str | None:
        return self.reason


TestStageResultType = TypeVar(
    "TestStageResultType",
    bound=TestSuccessStudentStageResult | TestFailureStudentStageResult,
)
