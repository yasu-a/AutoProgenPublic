from abc import ABC, abstractmethod
from collections import OrderedDict
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import datetime
from typing import TypeVar

from autoprogen.domain.error.stage.base import StageError
from autoprogen.domain.error.stage.build import BuildStageError
from autoprogen.domain.error.stage.compile import CompileStageError
from autoprogen.domain.error.stage.execute import ExecuteStageError
from autoprogen.domain.error.stage.test import TestStageError
from autoprogen.domain.model.project_settings import SourceCodeCheckIdentifier
from autoprogen.domain.model.output_file import OutputFileCollection
from autoprogen.domain.model.stage import AbstractStage, BuildStage, CompileStage, ExecuteStage, TestStage
from autoprogen.domain.model.test_result_output_file_entry import AbstractTestResultOutputFileEntry
from autoprogen.domain.model.value import FileID, StudentID, TestCaseID
from autoprogen.domain.service.stage_error_codec import StageErrorCodec, StageErrorRecord


def _stage_error_to_json(error: StageError) -> dict:
    """構造化ステージエラーをJSON互換の辞書へ変換する。"""
    record = StageErrorCodec().encode(error)
    return {
        "error_group_id": record.error_group_id,
        "error_type_id": record.error_type_id,
        "params": record.params,
    }


def _stage_error_from_json(body: dict) -> StageError:
    """JSON互換の辞書から構造化ステージエラーを復元する。"""
    return StageErrorCodec().decode(StageErrorRecord(
        error_group_id=body["error_group_id"],
        error_type_id=body["error_type_id"],
        params=body["params"],
    ))


@dataclass(slots=True)
class AbstractStudentStageResult(ABC):  # 各ステージの結果の基底クラス
    student_id: StudentID  # TODO: remove this  student_idはStudentStagePathResultで管理され、StudentStageResultはStudentStagePathResultの中の値オブジェクトに過ぎない
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
    # ステージ失敗の種類と固有情報を保持する構造化エラー。
    error: StageError

    @property
    def is_success(self) -> bool:
        return False


@dataclass(slots=True)
class BuildSuccessStudentStageResult(AbstractSuccessStudentStageResult):  # 生徒ごと
    submission_folder_checksum: int

    # noinspection DuplicatedCode
    def __post_init__(self):
        assert isinstance(self.student_id, StudentID), \
            (self.student_id, type(self.student_id))
        assert isinstance(self.stage, BuildStage), \
            (self.stage, type(self.stage))
        assert isinstance(self.submission_folder_checksum, int), \
            (self.submission_folder_checksum, type(self.submission_folder_checksum))

    @classmethod
    def create_instance(cls, *, student_id: StudentID, submission_folder_checksum: int):
        return cls(
            student_id=student_id,
            stage=BuildStage(),
            submission_folder_checksum=submission_folder_checksum,
        )

    def to_json(self):
        """BUILD成功結果をJSON互換の辞書へ変換する。"""
        return {
            "student_id": self.student_id.to_json(),
            "stage": self.stage.to_json(),
            "submission_folder_hash": self.submission_folder_checksum,
        }

    @classmethod
    def from_json(cls, body):
        """JSON互換の辞書からBUILD成功結果を復元する。"""
        return cls(
            student_id=StudentID.from_json(body["student_id"]),
            stage=AbstractStage.from_json(body["stage"]),
            submission_folder_checksum=body["submission_folder_hash"],
        )


@dataclass(slots=True)
class BuildFailureStudentStageResult(AbstractFailureStudentStageResult):  # 生徒ごと
    # noinspection DuplicatedCode
    def __post_init__(self):
        """学生ID、ステージ、構造化エラーの型を検証する。"""
        assert isinstance(self.student_id, StudentID), \
            (self.student_id, type(self.student_id))
        assert isinstance(self.stage, BuildStage), \
            (self.stage, type(self.stage))
        assert isinstance(self.error, BuildStageError), \
            (self.error, type(self.error))

    @classmethod
    def create_instance(cls, *, student_id: StudentID, error: BuildStageError):
        """BUILDの構造化エラーを持つ失敗結果を作成する。"""
        return cls(
            student_id=student_id,
            stage=BuildStage(),
            error=error,
        )

    def to_json(self):
        """BUILD失敗結果をJSON互換の辞書へ変換する。"""
        return {
            "student_id": self.student_id.to_json(),
            "stage": self.stage.to_json(),
            "error": _stage_error_to_json(self.error),
        }

    @classmethod
    def from_json(cls, body):
        """JSON互換の辞書からBUILD失敗結果を復元する。"""
        return cls(
            student_id=StudentID.from_json(body["student_id"]),
            stage=AbstractStage.from_json(body["stage"]),
            error=_stage_error_from_json(body["error"]),
        )


BuildStageResultType = TypeVar(
    "BuildStageResultType",
    bound=BuildSuccessStudentStageResult | BuildFailureStudentStageResult,
)


class SourceCodeCheckPolicy:
    """COMPILE時に抑制されていた安全性チェック規則を保持する値オブジェクト。"""

    __slots__ = ("_identifiers",)

    # 外部から変更できない、抑制対象の規則識別子集合。
    _identifiers: frozenset[SourceCodeCheckIdentifier]

    def __init__(
            self,
            identifiers: Iterable[SourceCodeCheckIdentifier] = (),
    ) -> None:
        """規則識別子を不変集合として取り込み、外部からの変更を遮断する。"""
        values = frozenset(identifiers)
        if any(not isinstance(value, SourceCodeCheckIdentifier) for value in values):
            raise TypeError("identifiersの要素はSourceCodeCheckIdentifierである必要があります")
        self._identifiers = values

    def __contains__(self, value: object) -> bool:
        """指定された規則識別子を保持しているか返す。"""
        return value in self._identifiers

    def __iter__(self) -> Iterator[SourceCodeCheckIdentifier]:
        """保持している規則識別子を反復する。"""
        return iter(self._identifiers)

    def __len__(self) -> int:
        """保持している規則識別子の数を返す。"""
        return len(self._identifiers)

    def __bool__(self) -> bool:
        """一件以上の規則識別子を保持している場合にTrueを返す。"""
        return bool(self._identifiers)

    def __eq__(self, other: object) -> bool:
        """保持している不変集合の内容で等価性を判定する。"""
        if isinstance(other, SourceCodeCheckPolicy):
            other = other._identifiers
        return self._identifiers == other

    def __hash__(self) -> int:
        """保持している不変集合と同じハッシュ値を返す。"""
        return hash(self._identifiers)

    def __repr__(self) -> str:
        """デバッグ時に保持内容を確認できる文字列表現を返す。"""
        return f"{type(self).__name__}({self._identifiers!r})"

    def to_json(self) -> list[dict[str, str]]:
        """規則識別子を安定した順序のJSON互換リストへ変換する。"""
        return [
            identifier.to_json()
            for identifier in sorted(
                self._identifiers,
                key=lambda item: (item.group_id, item.check_id),
            )
        ]

    @classmethod
    def from_json(cls, body: list[dict[str, str]]) -> "SourceCodeCheckPolicy":
        """JSON互換リストから安全性チェック方針を復元する。"""
        if type(body) is not list:
            raise TypeError("security_check_policyはlistである必要があります")
        return cls(
            SourceCodeCheckIdentifier.from_json(item)
            for item in body
        )


@dataclass(slots=True)
class CompileSuccessStudentStageResult(AbstractSuccessStudentStageResult):  # 生徒ごと
    # コンパイラが出力した標準出力・標準エラーの結合文字列。
    output: str
    # コンパイル時に抑制されていた安全性チェック規則。
    security_check_policy: SourceCodeCheckPolicy
    # 許可済みソースとして安全性チェックを省略したか。
    security_check_skipped: bool

    # noinspection DuplicatedCode
    def __post_init__(self):
        """COMPILE成功結果の各フィールド型を検証する。"""
        assert isinstance(self.student_id, StudentID), \
            (self.student_id, type(self.student_id))
        assert isinstance(self.stage, CompileStage), \
            (self.stage, type(self.stage))
        assert isinstance(self.output, str), \
            (self.output, type(self.output))
        assert isinstance(self.security_check_policy, SourceCodeCheckPolicy), \
            (self.security_check_policy, type(self.security_check_policy))
        assert isinstance(self.security_check_skipped, bool), \
            (self.security_check_skipped, type(self.security_check_skipped))

    @classmethod
    def create_instance(
            cls,
            *,
            student_id: StudentID,
            output: str,
            security_check_policy: SourceCodeCheckPolicy = SourceCodeCheckPolicy(),
            security_check_skipped: bool = False,
    ):
        """出力と実行時の安全性チェック状態を持つ成功結果を作成する。"""
        return cls(
            student_id=student_id,
            stage=CompileStage(),
            output=output,
            security_check_policy=security_check_policy,
            security_check_skipped=security_check_skipped,
        )

    def to_json(self):
        """COMPILE成功結果をJSON互換の辞書へ変換する。"""
        return {
            "student_id": self.student_id.to_json(),
            "stage": self.stage.to_json(),
            "output": self.output,
            "security_check_policy": self.security_check_policy.to_json(),
            "security_check_skipped": self.security_check_skipped,
        }

    @classmethod
    def from_json(cls, body):
        """JSON互換の辞書からCOMPILE成功結果を復元する。"""
        return cls(
            student_id=StudentID.from_json(body["student_id"]),
            stage=AbstractStage.from_json(body["stage"]),
            output=body["output"],
            security_check_policy=SourceCodeCheckPolicy.from_json(
                body["security_check_policy"],
            ),
            security_check_skipped=body["security_check_skipped"],
        )


@dataclass(slots=True)
class CompileFailureStudentStageResult(AbstractFailureStudentStageResult):  # 生徒ごと
    output: str

    # noinspection DuplicatedCode
    def __post_init__(self):
        """学生ID、ステージ、構造化エラー、出力の型を検証する。"""
        assert isinstance(self.student_id, StudentID), \
            (self.student_id, type(self.student_id))
        assert isinstance(self.stage, CompileStage), \
            (self.stage, type(self.stage))
        assert isinstance(self.error, CompileStageError), \
            (self.error, type(self.error))
        assert isinstance(self.output, str), \
            (self.output, type(self.output))

    @classmethod
    def create_instance(
            cls,
            *,
            student_id: StudentID,
            error: CompileStageError,
            output: str,
    ):
        """COMPILEの構造化エラーとコンパイラ出力を持つ失敗結果を作成する。"""
        return cls(
            student_id=student_id,
            stage=CompileStage(),
            error=error,
            output=output,
        )

    def to_json(self):
        """COMPILE失敗結果をJSON互換の辞書へ変換する。"""
        return {
            "student_id": self.student_id.to_json(),
            "stage": self.stage.to_json(),
            "error": _stage_error_to_json(self.error),
            "output": self.output,
        }

    @classmethod
    def from_json(cls, body):
        """JSON互換の辞書からCOMPILE失敗結果を復元する。"""
        return cls(
            student_id=StudentID.from_json(body["student_id"]),
            stage=AbstractStage.from_json(body["stage"]),
            error=_stage_error_from_json(body["error"]),
            output=body["output"],
        )


CompileStageResultType = TypeVar(
    "CompileStageResultType",
    bound=CompileSuccessStudentStageResult | CompileFailureStudentStageResult,
)


@dataclass(slots=True)
class ExecuteSuccessStudentStageResult(AbstractSuccessStudentStageResult):  # 生徒・テストケースごと
    execute_config_mtime: datetime
    output_file_collection: OutputFileCollection

    # noinspection DuplicatedCode
    def __post_init__(self):
        assert isinstance(self.student_id, StudentID), \
            (self.student_id, type(self.student_id))
        assert isinstance(self.stage, ExecuteStage), \
            (self.stage, type(self.stage))
        assert isinstance(self.execute_config_mtime, datetime), \
            (self.execute_config_mtime, type(self.execute_config_mtime))
        assert isinstance(self.output_file_collection, OutputFileCollection), \
            (self.output_file_collection, type(self.output_file_collection))

    @classmethod
    def create_instance(
            cls,
            *,
            student_id: StudentID,
            testcase_id: TestCaseID,
            execute_config_mtime: datetime,
            output_file_collection: OutputFileCollection,
    ):
        return cls(
            student_id=student_id,
            stage=ExecuteStage(testcase_id=testcase_id),
            execute_config_mtime=execute_config_mtime,
            output_file_collection=output_file_collection,
        )

    def to_json(self):
        return {
            "student_id": self.student_id.to_json(),
            "stage": self.stage.to_json(),
            "execute_config_mtime": self.execute_config_mtime.isoformat(),
            "output_file_collection": self.output_file_collection.to_json(),
        }

    @classmethod
    def from_json(cls, body):
        return cls(
            student_id=StudentID.from_json(body["student_id"]),
            stage=AbstractStage.from_json(body["stage"]),
            execute_config_mtime=datetime.fromisoformat(body["execute_config_mtime"]),
            output_file_collection=OutputFileCollection.from_json(body["output_file_collection"]),
        )

    @property
    def testcase_id(self) -> TestCaseID:
        assert isinstance(self.stage, ExecuteStage)
        return self.stage.testcase_id


@dataclass(slots=True)
class ExecuteFailureStudentStageResult(AbstractFailureStudentStageResult):  # 生徒・テストケースごと
    # noinspection DuplicatedCode
    def __post_init__(self):
        """学生ID、ステージ、構造化エラーの型を検証する。"""
        assert isinstance(self.student_id, StudentID), \
            (self.student_id, type(self.student_id))
        assert isinstance(self.stage, ExecuteStage), \
            (self.stage, type(self.stage))
        assert isinstance(self.error, ExecuteStageError), \
            (self.error, type(self.error))

    @classmethod
    def create_instance(
            cls,
            *,
            student_id: StudentID,
            testcase_id: TestCaseID,
            error: ExecuteStageError,
    ):
        """EXECUTEの構造化エラーを持つ失敗結果を作成する。"""
        return cls(
            student_id=student_id,
            stage=ExecuteStage(testcase_id=testcase_id),
            error=error,
        )

    def to_json(self) -> dict:
        """EXECUTE失敗結果をJSON互換の辞書へ変換する。"""
        return {
            "student_id": self.student_id.to_json(),
            "stage": self.stage.to_json(),
            "error": _stage_error_to_json(self.error),
        }

    @classmethod
    def from_json(cls, body: dict):
        """JSON互換の辞書からEXECUTE失敗結果を復元する。"""
        return cls(
            student_id=StudentID.from_json(body["student_id"]),
            stage=AbstractStage.from_json(body["stage"]),
            error=_stage_error_from_json(body["error"]),
        )

    @property
    def testcase_id(self) -> TestCaseID:
        assert isinstance(self.stage, ExecuteStage)
        return self.stage.testcase_id


ExecuteStageResultType = TypeVar(
    "ExecuteStageResultType",
    bound=ExecuteSuccessStudentStageResult | ExecuteFailureStudentStageResult,
)


class TestResultOutputFileCollection:
    def __init__(self, it=()):
        self._mapping: OrderedDict[FileID, AbstractTestResultOutputFileEntry] = OrderedDict()
        for item in it:
            self.put(item)

    def put(self, item: AbstractTestResultOutputFileEntry) -> None:
        self._mapping[item.file_id] = item

    def find(self, file_id: FileID) -> AbstractTestResultOutputFileEntry:
        return self._mapping[file_id]

    def has(self, file_id: FileID) -> bool:
        return file_id in self._mapping

    @property
    def file_ids(self) -> list[FileID]:
        return list(self._mapping.keys())

    def items(self):
        return self._mapping.items()

    def to_json(self) -> dict:
        return {
            file_id.to_json(): result.to_json()
            for file_id, result in self._mapping.items()
        }

    @classmethod
    def from_json(cls, body: dict) -> "TestResultOutputFileCollection":
        return cls(
            AbstractTestResultOutputFileEntry.from_json(result_body)
            for file_id_str, result_body in body.items()
        )

    @property
    def is_accepted(self) -> bool:  # テストケースが正解かどうか
        for file_id, file_entry in self._mapping.items():
            try:
                is_test_result_accepted = file_entry.is_test_result_accepted
            except ValueError:  # 判定不可
                continue
            else:
                if not is_test_result_accepted:
                    return False
        return True


@dataclass(slots=True)
class TestSuccessStudentStageResult(AbstractSuccessStudentStageResult):  # 生徒・テストケースごと
    test_config_mtime: datetime
    test_result_output_file_collection: TestResultOutputFileCollection

    # noinspection DuplicatedCode
    def __post_init__(self):
        assert isinstance(self.student_id, StudentID), \
            (self.student_id, type(self.student_id))
        assert isinstance(self.stage, TestStage), \
            (self.stage, type(self.stage))
        assert isinstance(self.test_config_mtime, datetime), \
            (self.test_config_mtime, type(self.test_config_mtime))
        assert isinstance(self.test_result_output_file_collection, TestResultOutputFileCollection), \
            (self.test_result_output_file_collection, type(self.test_result_output_file_collection))

    @classmethod
    def create_instance(
            cls,
            *,
            student_id: StudentID,
            testcase_id: TestCaseID,
            test_config_mtime: datetime,
            test_result_output_file_collection: TestResultOutputFileCollection,
    ):
        return cls(
            student_id=student_id,
            stage=TestStage(testcase_id=testcase_id),
            test_config_mtime=test_config_mtime,
            test_result_output_file_collection=test_result_output_file_collection,
        )

    def to_json(self) -> dict:
        return {
            "student_id": self.student_id.to_json(),
            "stage": self.stage.to_json(),
            "test_config_mtime": self.test_config_mtime.isoformat(),
            "test_result_output_file_collection": self.test_result_output_file_collection.to_json(),
        }

    @classmethod
    def from_json(cls, body: dict) -> "TestSuccessStudentStageResult":
        return cls(
            student_id=StudentID.from_json(body["student_id"]),
            stage=AbstractStage.from_json(body["stage"]),
            test_config_mtime=datetime.fromisoformat(body["test_config_mtime"]),
            test_result_output_file_collection=TestResultOutputFileCollection.from_json(
                body["test_result_output_file_collection"],
            ),
        )

    @property
    def testcase_id(self) -> TestCaseID:
        assert isinstance(self.stage, TestStage)
        return self.stage.testcase_id

    @property
    def is_accepted(self) -> bool:
        return self.test_result_output_file_collection.is_accepted


@dataclass(slots=True)
class TestFailureStudentStageResult(AbstractFailureStudentStageResult):  # 生徒・テストケースごと
    # noinspection DuplicatedCode
    def __post_init__(self):
        """学生ID、ステージ、構造化エラーの型を検証する。"""
        assert isinstance(self.student_id, StudentID), \
            (self.student_id, type(self.student_id))
        assert isinstance(self.stage, TestStage), \
            (self.stage, type(self.stage))
        assert isinstance(self.error, TestStageError), \
            (self.error, type(self.error))

    @classmethod
    def create_instance(
            cls,
            *,
            student_id: StudentID,
            testcase_id: TestCaseID,
            error: TestStageError,
    ):
        """TESTの構造化エラーを持つ失敗結果を作成する。"""
        return cls(
            student_id=student_id,
            stage=TestStage(testcase_id=testcase_id),
            error=error,
        )

    def to_json(self) -> dict:
        """TEST失敗結果をJSON互換の辞書へ変換する。"""
        return {
            "student_id": self.student_id.to_json(),
            "stage": self.stage.to_json(),
            "error": _stage_error_to_json(self.error),
        }

    @classmethod
    def from_json(cls, body: dict) -> "TestFailureStudentStageResult":
        """JSON互換の辞書からTEST失敗結果を復元する。"""
        return cls(
            student_id=StudentID.from_json(body["student_id"]),
            stage=AbstractStage.from_json(body["stage"]),
            error=_stage_error_from_json(body["error"]),
        )

    @property
    def testcase_id(self) -> TestCaseID:
        assert isinstance(self.stage, TestStage)
        return self.stage.testcase_id


TestStageResultType = TypeVar(
    "TestStageResultType",
    bound=TestSuccessStudentStageResult | TestFailureStudentStageResult,
)
