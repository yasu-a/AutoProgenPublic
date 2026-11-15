from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime

from autoprogen.domain.error.stage.build import BuildStageError
from autoprogen.domain.error.stage.compile import CompileStageError
from autoprogen.domain.error.stage.execute import ExecuteStageError
from autoprogen.domain.error.stage.test import TestStageError
from autoprogen.domain.model.project_settings import SourceCodeCheckSuppressions
from autoprogen.domain.model.output_file import OutputFileCollection
from autoprogen.domain.model.stage import AbstractStage, BuildStage, CompileStage, ExecuteStage, TestStage
from autoprogen.domain.model.test_result_output_file_entry import AbstractTestResultOutputFileEntry
from autoprogen.domain.model.value import FileID, StudentID, TestCaseID


@dataclass(slots=True)
class AbstractStudentStageResult(ABC):  # 各ステージの結果の基底クラス
    student_id: StudentID  # TODO: remove this  student_idはStudentStagePathResultで管理され、StudentStageResultはStudentStagePathResultの中の値オブジェクトに過ぎない
    stage: AbstractStage

    @property
    @abstractmethod
    def is_success(self) -> bool:
        raise NotImplementedError()


@dataclass(slots=True)
class BuildStudentStageResult(AbstractStudentStageResult):  # 生徒ごと
    """BUILD実行時の提出状態と、成功または構造化エラーを保持する。"""

    # BUILD実行時の提出フォルダのチェックサム。
    submission_folder_checksum: int
    # BUILDが成功した場合はNone、失敗した場合は原因となった構造化エラー。
    error: BuildStageError | None

    def __post_init__(self) -> None:
        """学生、ステージ、チェックサム、エラーの型と成功条件を検証する。"""
        if not isinstance(self.student_id, StudentID):
            raise TypeError("student_idはStudentIDである必要があります")
        if not isinstance(self.stage, BuildStage):
            raise TypeError("stageはBuildStageである必要があります")
        if not isinstance(self.submission_folder_checksum, int):
            raise TypeError("submission_folder_checksumはintである必要があります")
        if self.error is not None:
            if not isinstance(self.error, BuildStageError):
                raise TypeError("errorはBuildStageErrorまたはNoneである必要があります")

    @property
    def is_success(self) -> bool:
        """構造化エラーがなければBUILD成功として返す。"""
        return self.error is None

    def is_outdated(self, *, current_submission_folder_checksum: int) -> bool:
        """提出フォルダの内容がBUILD実行時から変化したか判定する。"""
        return self.submission_folder_checksum != current_submission_folder_checksum

    @classmethod
    def create_instance(
            cls,
            *,
            student_id: StudentID,
            submission_folder_checksum: int,
            error: BuildStageError | None,
    ) -> "BuildStudentStageResult":
        """BUILD実行時のチェックサムとエラーから結果を生成する。"""
        return cls(
            student_id=student_id,
            stage=BuildStage(),
            submission_folder_checksum=submission_folder_checksum,
            error=error,
        )

@dataclass(slots=True)
class CompileStudentStageResult(AbstractStudentStageResult):  # 生徒ごと
    """COMPILEの出力、実行時条件、成功または構造化エラーを保持する。"""

    # コンパイラが出力した標準出力・標準エラーの結合文字列。
    output: str
    # コンパイル時に抑制されていた安全性チェック規則。
    suppressed_source_code_checks: SourceCodeCheckSuppressions
    # 許可済みソースとして安全性チェックを省略したか。
    source_code_check_skipped: bool
    # COMPILEが成功した場合はNone、失敗した場合は原因となった構造化エラー。
    error: CompileStageError | None

    def __post_init__(self) -> None:
        """COMPILE結果を構成する各フィールドの型を検証する。"""
        if not isinstance(self.student_id, StudentID):
            raise TypeError("student_idはStudentIDである必要があります")
        if not isinstance(self.stage, CompileStage):
            raise TypeError("stageはCompileStageである必要があります")
        if not isinstance(self.output, str):
            raise TypeError("outputはstrである必要があります")
        if not isinstance(
            self.suppressed_source_code_checks,
            SourceCodeCheckSuppressions,
        ):
            raise TypeError(
                "suppressed_source_code_checksはSourceCodeCheckSuppressionsである必要があります"
            )
        if not isinstance(self.source_code_check_skipped, bool):
            raise TypeError("source_code_check_skippedはboolである必要があります")
        if self.error is not None:
            if not isinstance(self.error, CompileStageError):
                raise TypeError("errorはCompileStageErrorまたはNoneである必要があります")

    @property
    def is_success(self) -> bool:
        """構造化エラーがなければCOMPILE成功として返す。"""
        return self.error is None

    def is_outdated(
            self,
            *,
            current_suppressed_source_code_checks: SourceCodeCheckSuppressions,
            current_source_code_check_skipped: bool,
    ) -> bool:
        """安全性チェック設定がCOMPILE実行時から変化したか判定する。"""
        return (
            self.suppressed_source_code_checks != current_suppressed_source_code_checks
            or self.source_code_check_skipped != current_source_code_check_skipped
        )

    @classmethod
    def create_instance(
            cls,
            *,
            student_id: StudentID,
            output: str,
            suppressed_source_code_checks: SourceCodeCheckSuppressions,
            source_code_check_skipped: bool,
            error: CompileStageError | None,
    ) -> "CompileStudentStageResult":
        """出力、実行時の安全性チェック状態、エラーから結果を生成する。"""
        return cls(
            student_id=student_id,
            stage=CompileStage(),
            output=output,
            suppressed_source_code_checks=suppressed_source_code_checks,
            source_code_check_skipped=source_code_check_skipped,
            error=error,
        )


@dataclass(slots=True)
class ExecuteStudentStageResult(AbstractStudentStageResult):  # 生徒・テストケースごと
    """EXECUTEの実行条件と、成功時の出力または失敗時のエラーを保持する。"""

    # EXECUTE実行時の実行設定ファイルの更新日時。
    execute_config_mtime: datetime
    # 成功時に生成された出力ファイル群。失敗時はNone。
    output_file_collection: OutputFileCollection | None
    # 成功時はNone、失敗時は原因となった構造化エラー。
    error: ExecuteStageError | None

    # noinspection DuplicatedCode
    def __post_init__(self) -> None:
        """学生、ステージ、実行条件、結果データの型を検証する。"""
        if not isinstance(self.student_id, StudentID):
            raise TypeError("student_idはStudentIDである必要があります")
        if not isinstance(self.stage, ExecuteStage):
            raise TypeError("stageはExecuteStageである必要があります")
        if not isinstance(self.execute_config_mtime, datetime):
            raise TypeError("execute_config_mtimeはdatetimeである必要があります")
        if self.output_file_collection is not None:
            if not isinstance(self.output_file_collection, OutputFileCollection):
                raise TypeError(
                    "output_file_collectionはOutputFileCollectionまたはNoneである必要があります"
                )
        if self.error is not None:
            if not isinstance(self.error, ExecuteStageError):
                raise TypeError("errorはExecuteStageErrorまたはNoneである必要があります")

        if self.error is None:
            if self.output_file_collection is None:
                raise ValueError("成功したEXECUTE結果には出力ファイル群が必要です")
        elif self.output_file_collection is not None:
            raise ValueError("失敗したEXECUTE結果は出力ファイル群を保持できません")

    @property
    def is_success(self) -> bool:
        """構造化エラーがなければEXECUTE成功として返す。"""
        return self.error is None

    def is_outdated(self, *, current_execute_config_mtime: datetime) -> bool:
        """実行設定がEXECUTE実行時から変化したか判定する。"""
        return self.execute_config_mtime != current_execute_config_mtime

    @classmethod
    def create_instance(
            cls,
            *,
            student_id: StudentID,
            testcase_id: TestCaseID,
            execute_config_mtime: datetime,
            output_file_collection: OutputFileCollection | None,
            error: ExecuteStageError | None,
    ) -> "ExecuteStudentStageResult":
        """実行条件、出力ファイル群、エラーからEXECUTE結果を作成する。"""
        return cls(
            student_id=student_id,
            stage=ExecuteStage(testcase_id=testcase_id),
            execute_config_mtime=execute_config_mtime,
            output_file_collection=output_file_collection,
            error=error,
        )

    @property
    def testcase_id(self) -> TestCaseID:
        """結果が属するテストケースIDを返す。"""
        assert isinstance(self.stage, ExecuteStage)
        return self.stage.testcase_id


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
class TestStudentStageResult(AbstractStudentStageResult):  # 生徒・テストケースごと
    """TESTの実行条件と、成功時の照合結果または失敗時のエラーを保持する。"""

    # TEST実行時のテスト設定ファイルの更新日時。
    test_config_mtime: datetime
    # 成功時の出力ファイル別照合結果。失敗時はNone。
    test_result_output_file_collection: TestResultOutputFileCollection | None
    # 成功時はNone、失敗時は原因となった構造化エラー。
    error: TestStageError | None

    # noinspection DuplicatedCode
    def __post_init__(self) -> None:
        """学生、ステージ、実行条件、結果データの型と組み合わせを検証する。"""
        if not isinstance(self.student_id, StudentID):
            raise TypeError("student_idはStudentIDである必要があります")
        if not isinstance(self.stage, TestStage):
            raise TypeError("stageはTestStageである必要があります")
        if not isinstance(self.test_config_mtime, datetime):
            raise TypeError("test_config_mtimeはdatetimeである必要があります")
        if self.test_result_output_file_collection is not None:
            if not isinstance(
                self.test_result_output_file_collection,
                TestResultOutputFileCollection,
            ):
                raise TypeError(
                    "test_result_output_file_collectionは"
                    "TestResultOutputFileCollectionまたはNoneである必要があります"
                )
        if self.error is not None:
            if not isinstance(self.error, TestStageError):
                raise TypeError("errorはTestStageErrorまたはNoneである必要があります")

        if self.error is None:
            if self.test_result_output_file_collection is None:
                raise ValueError("成功したTEST結果には出力ファイル別の照合結果が必要です")
        elif self.test_result_output_file_collection is not None:
            raise ValueError("失敗したTEST結果は出力ファイル別の照合結果を保持できません")

    @property
    def is_success(self) -> bool:
        """構造化エラーがなければTEST成功として返す。"""
        return self.error is None

    def is_outdated(self, *, current_test_config_mtime: datetime) -> bool:
        """テスト設定がTEST実行時から変化したか判定する。"""
        return self.test_config_mtime != current_test_config_mtime

    @classmethod
    def create_instance(
            cls,
            *,
            student_id: StudentID,
            testcase_id: TestCaseID,
            test_config_mtime: datetime,
            test_result_output_file_collection: TestResultOutputFileCollection | None,
            error: TestStageError | None,
    ) -> "TestStudentStageResult":
        """実行条件、照合結果、エラーからTEST結果を作成する。"""
        return cls(
            student_id=student_id,
            stage=TestStage(testcase_id=testcase_id),
            test_config_mtime=test_config_mtime,
            test_result_output_file_collection=test_result_output_file_collection,
            error=error,
        )

    @property
    def testcase_id(self) -> TestCaseID:
        """結果が属するテストケースIDを返す。"""
        assert isinstance(self.stage, TestStage)
        return self.stage.testcase_id

    @property
    def is_accepted(self) -> bool:
        """成功したTEST結果がすべての判定対象を受理したか返す。"""
        # このプロパティは成功結果に対して使用する契約としてOptionalの型を絞り込む。
        assert self.test_result_output_file_collection is not None
        return self.test_result_output_file_collection.is_accepted
