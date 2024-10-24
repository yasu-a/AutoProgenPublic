from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import TypeVar

from domain.models.output_file import OutputFileMapping
from domain.models.stages import AbstractStage, BuildStage, CompileStage, ExecuteStage, TestStage
from domain.models.values import FileID, StudentID


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
        return None


@dataclass(slots=True)
class BuildSuccessStudentStageResult(AbstractSuccessStudentStageResult):  # 生徒ごと
    submission_folder_hash: int

    def __post_init__(self):
        assert isinstance(self.stage, BuildStage)

    def has_submission_folder_hash_of(self, h: int) -> bool:
        return self.submission_folder_hash == h

    def to_json(self):
        return {
            "student_id": self.student_id.to_json(),
            "stage": self.stage.to_json(),
            "submission_folder_hash": self.submission_folder_hash,
        }

    @classmethod
    def from_json(cls, body):
        return cls(
            student_id=StudentID.from_json(body["student_id"]),
            stage=AbstractStage.from_json(body["stage"]),
            submission_folder_hash=body["submission_folder_hash"],
        )


@dataclass(slots=True)
class BuildFailureStudentStageResult(AbstractFailureStudentStageResult):  # 生徒ごと
    def __post_init__(self):
        assert isinstance(self.stage, BuildStage)

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


BuildStageResultType = TypeVar(
    "BuildStageResultType",
    bound=BuildSuccessStudentStageResult | BuildFailureStudentStageResult,
)


@dataclass(slots=True)
class CompileSuccessStudentStageResult(AbstractSuccessStudentStageResult):  # 生徒ごと
    output: str

    def __post_init__(self):
        assert isinstance(self.stage, CompileStage)

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
    execute_config_mtime: datetime

    def __post_init__(self):
        assert isinstance(self.stage, ExecuteStage)

    def to_json(self) -> dict:
        return {
            "student_id": self.student_id.to_json(),
            "stage": self.stage.to_json(),
            "execute_config_mtime": self.execute_config_mtime.isoformat(),
            "reason": self.reason,
        }

    @classmethod
    def from_json(cls, body: dict):
        return cls(
            student_id=StudentID.from_json(body["student_id"]),
            stage=AbstractStage.from_json(body["stage"]),
            execute_config_mtime=datetime.fromisoformat(body["execute_config_mtime"]),
            reason=body["reason"],
        )


ExecuteStageResultType = TypeVar(
    "ExecuteStageResultType",
    bound=ExecuteSuccessStudentStageResult | ExecuteFailureStudentStageResult,
)


@dataclass(slots=True)
class MatchedToken:
    match_begin: int
    match_end: int
    expected_token_index: int

    def to_json(self) -> dict:
        return dict(
            match_begin=self.match_begin,
            match_end=self.match_end,
            expected_token_index=self.expected_token_index,
        )

    @classmethod
    def from_json(cls, body: dict) -> "MatchedToken":
        return cls(
            match_begin=body["match_begin"],
            match_end=body["match_end"],
            expected_token_index=body["expected_token_index"],
        )


@dataclass(slots=True)
class NonmatchedToken:
    expected_token_index: int

    def to_json(self) -> dict:
        return dict(
            expected_token_index=self.expected_token_index,
        )

    @classmethod
    def from_json(cls, body: dict) -> "NonmatchedToken":
        return cls(
            expected_token_index=body["expected_token_index"],
        )


@dataclass(slots=True)
class OutputFileTestResult:
    file_id: FileID
    matched_tokens: list[MatchedToken]
    nonmatched_tokens: list[NonmatchedToken]

    def to_json(self) -> dict:
        return dict(
            file_id=self.file_id.to_json(),
            matched_tokens=[token.to_json() for token in self.matched_tokens],
            nonmatched_tokens=[token.to_json() for token in self.nonmatched_tokens],
        )

    @classmethod
    def from_json(cls, body: dict) -> "OutputFileTestResult":
        return cls(
            file_id=FileID.from_json(body["file_id"]),
            matched_tokens=[
                MatchedToken.from_json(token_body)
                for token_body in body["matched_tokens"]
            ],
            nonmatched_tokens=[
                NonmatchedToken.from_json(token_body)
                for token_body in body["nonmatched_tokens"]
            ],
        )

    @property
    def is_accepted(self) -> bool:  # 正解かどうか
        return len(self.nonmatched_tokens) == 0


class OutputFileTestResultMapping(dict[FileID, OutputFileTestResult | None]):  # 出力ファイルがない場合はNone
    def to_json(self) -> dict[str, dict]:
        return {
            file_id.to_json(): (
                result.to_json()
                if result is not None
                else None
            )
            for file_id, result in self.items()
        }

    @classmethod
    def from_json(cls, body: dict) -> "OutputFileTestResultMapping":
        return cls({
            FileID.from_json(file_id_str): (
                None
                if result_body is None
                else OutputFileTestResult.from_json(result_body)
            )
            for file_id_str, result_body in body.items()
        })

    @property
    def is_accepted(self) -> bool:  # テストケースが正解かどうか（全ての出力が正解かどうか）
        return all(result is not None and result.is_accepted for result in self.values())


class TestSummary(Enum):
    WRONG_ANSWER = "正解条件を満たしていません"
    ACCEPTED = "正解です"
    UNTESTABLE = "テストできません"


@dataclass(slots=True)
class TestSuccessStudentStageResult(AbstractSuccessStudentStageResult):  # 生徒・テストケースごと
    test_config_mtime: datetime
    output_file_test_results: OutputFileTestResultMapping

    def __post_init__(self):
        assert isinstance(self.stage, TestStage)

    @property
    def summary(self) -> TestSummary:
        if self.is_success:
            if self.output_file_test_results.is_accepted:
                return TestSummary.ACCEPTED
            else:
                return TestSummary.WRONG_ANSWER
        else:
            return TestSummary.UNTESTABLE

    def to_json(self) -> dict:
        return {
            "student_id": self.student_id.to_json(),
            "stage": self.stage.to_json(),
            "test_config_mtime": self.test_config_mtime.isoformat(),
            "output_file_test_results": self.output_file_test_results.to_json(),
        }

    @classmethod
    def from_json(cls, body: dict) -> "TestSuccessStudentStageResult":
        return cls(
            student_id=StudentID.from_json(body["student_id"]),
            stage=AbstractStage.from_json(body["stage"]),
            test_config_mtime=datetime.fromisoformat(body["test_config_mtime"]),
            output_file_test_results=OutputFileTestResultMapping.from_json(
                body["output_file_test_results"],
            ),
        )


@dataclass(slots=True)
class TestFailureStudentStageResult(AbstractFailureStudentStageResult):  # 生徒・テストケースごと
    test_config_mtime: datetime

    def __post_init__(self):
        assert isinstance(self.stage, TestStage)

    def to_json(self) -> dict:
        return {
            "student_id": self.student_id.to_json(),
            "stage": self.stage.to_json(),
            "test_config_mtime": self.test_config_mtime.isoformat(),
            "reason": self.reason,
        }

    @classmethod
    def from_json(cls, body: dict) -> "TestFailureStudentStageResult":
        return cls(
            student_id=StudentID.from_json(body["student_id"]),
            stage=AbstractStage.from_json(body["stage"]),
            test_config_mtime=datetime.fromisoformat(body["test_config_mtime"]),
            reason=body["reason"],
        )


TestStageResultType = TypeVar(
    "TestStageResultType",
    bound=TestSuccessStudentStageResult | TestFailureStudentStageResult,
)
