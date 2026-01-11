from datetime import datetime
from enum import Enum, auto

from shared.domain.model.stage import Stage
from shared.domain.validation import check_dict, check_type, check_enum
from shared.domain.value.identifier import StudentID, TestCaseID
from shared.domain.value.output_file import OutputFileCollection
from shared.domain.value.student_stage_result import TestResultOutputFileCollection


class StudentStageStatusFlag(Enum):
    """
    学生の各ステージにおける実行状態を表す列挙型。

    Attributes:
        UNFINISHED: 未実行、または実行中（結果が確定していない）。
        FINISHED_SUCCESS: 実行が完了し、成功した状態。
        FINISHED_FAILURE: 実行が完了したが、失敗した状態（コンパイルエラーやテスト不合格など）。
    """
    UNFINISHED = auto()
    FINISHED_SUCCESS = auto()
    FINISHED_FAILURE = auto()


class StudentStageStatusEntity:
    """
    学生一人の全ステージ（Build, Compile, Execute, Test）の進捗状況を集約したエンティティ。
    一覧画面での表示などに使用されます。

    Attributes:
        student_id (StudentID): 学生ID。
        build_status (StudentStageStatusFlag): フォルダ構成チェック（Build）の状態。
        compile_status (StudentStageStatusFlag): コンパイル（Compile）の状態。
        execute_status (dict[TestCaseID, StudentStageStatusFlag]): 
            各テストケースごとの実行（Execute）状態のマッピング。
        test_status (dict[TestCaseID, StudentStageStatusFlag]): 
            各テストケースごとの正誤判定（Test）状態のマッピング。
        timestamp (datetime | None): 
            このステータス情報の最終更新日時。
            一度も実行されていない初期状態（UNFINISHEDのみ）の場合は None となる。
    """

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
        check_type("student_id", self._student_id, expected_type=StudentID)
        check_enum("build_status", self.build_status,
                   enum_cls=StudentStageStatusFlag)
        check_enum("compile_status", self.compile_status,
                   enum_cls=StudentStageStatusFlag)
        check_dict(
            "execute_status", self.execute_status,
            expected_key_type=TestCaseID,
            expected_value_type=StudentStageStatusFlag
        )
        check_dict(
            "test_status", self.test_status,
            expected_key_type=TestCaseID,
            expected_value_type=StudentStageStatusFlag
        )
        check_type("timestamp", self.timestamp,
                   expected_type=datetime, nullable=True)


class AbstractStageResultEntity:
    """
    各ステージ結果エンティティの基底クラス。
    すべての結果に共通するフィールドとバリデーションロジックを持ちます。

    Attributes:
        student_id (StudentID): 学生ID。
        stage (Stage): 実行したステージの種類。
        testcase_id (TestCaseID | None): テストケースID（Execute/Testステージのみ必須）。
        is_success (bool): ステージ全体としての成功/失敗フラグ。
        timestamp (datetime): 実行完了日時。
        error_summary (str | None): 
            失敗時のエラー概要（例外メッセージの1行目など）。
            is_success=True（成功）の場合は None となる。
            is_success=False（失敗）の場合は値が入る。
    """

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

    def _validate(self):
        # 基本型チェック
        check_type("student_id", self._student_id, StudentID)
        check_enum("stage", self._stage, Stage)
        check_type("timestamp", self.timestamp, datetime)
        check_type("is_success", self.is_success, bool)
        check_type("error_summary", self.error_summary, str, nullable=True)

        # testcase_id の有無ルール
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

    @property
    def student_id(self) -> StudentID:
        return self._student_id

    @property
    def stage(self) -> Stage:
        return self._stage

    @property
    def testcase_id(self) -> TestCaseID | None:
        return self._testcase_id


class BuildStageResultEntity(AbstractStageResultEntity):
    """
    Buildステージ（提出フォルダの構成チェックなど）の結果エンティティ。

    Attributes:
        submission_folder_checksum (int | None): 
            提出フォルダの内容に基づいたチェックサム。
            - 成功時: 計算されたチェックサム値が入る。
            - 失敗時（ソースファイル取得失敗など）: None となる。
    """

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
        self._validate()

    def _validate(self):
        super()._validate()
        # 固有フィールドの型チェック
        check_type("submission_folder_checksum",
                   self.submission_folder_checksum, int, nullable=True)


class CompileStageResultEntity(AbstractStageResultEntity):
    """
    Compileステージ（コンパイル実行）の結果エンティティ。

    Attributes:
        output (str): 
            コンパイラの標準出力および標準エラー出力の内容。
            - 成功時: コンパイラの出力が入る。
            - 失敗時: 出力がない場合でも空文字("")が入るため、Noneになることはない。
    """

    def __init__(
            self,
            *,
            student_id: StudentID,
            output: str,  # Noneを許容しないよう変更
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
        self._validate()

    def _validate(self):
        super()._validate()
        # 固有フィールドの型チェック
        # nullable=True を削除
        check_type("output", self.output, str)


class ExecuteStageResultEntity(AbstractStageResultEntity):
    """
    Executeステージ（プログラム実行）の結果エンティティ。

    Attributes:
        execute_config_mtime (datetime | None): 
            実行時に使用された「実行設定（TestCaseConfig）」の更新日時。
            - 成功時: 設定ファイルのmtimeが入る。
            - 失敗時: None となる。
        output_file_collection (OutputFileCollection | None): 
            プログラム実行によって生成されたファイル群。
            - 成功時: 生成されたファイルコレクションが入る。
            - 失敗時（実行前クラッシュなど）: None となる。
    """

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
        self._validate()

    def _validate(self):
        super()._validate()
        # 固有フィールドの型チェック
        check_type("execute_config_mtime",
                   self.execute_config_mtime, datetime, nullable=True)
        check_type("output_file_collection", self.output_file_collection,
                   OutputFileCollection, nullable=True)


class TestStageResultEntity(AbstractStageResultEntity):
    """
    Testステージ（正解判定）の結果エンティティ。

    Attributes:
        test_config_mtime (datetime | None): 
            判定時に使用された「テスト設定（TestCaseConfig）」の更新日時。
            - 成功時: 設定ファイルのmtimeが入る。
            - 失敗時: None となる。
        test_result_output_file_collection (TestResultOutputFileCollection | None): 
            判定プロセスによって生成された結果ファイル群。
            - 成功時: 結果ファイルコレクションが入る。
            - 失敗時（判定不能など）: None となる。
        failure_reason (str | None): 
            不合格（Failure）となった場合の具体的な理由（例: "Output Mismatch"）。
            - is_success=True の場合: None。
            - is_success=False の場合: 理由を表す文字列が入る。
    """

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
        self._validate()

    def _validate(self):
        super()._validate()
        # 固有フィールドの型チェック
        check_type("test_config_mtime", self.test_config_mtime,
                   datetime, nullable=True)
        check_type("test_result_output_file_collection", self.test_result_output_file_collection,
                   TestResultOutputFileCollection, nullable=True)
        check_type("failure_reason", self.failure_reason, str, nullable=True)

    @property
    def is_accepted(self) -> bool:
        """
        テストケースが正解（AC: Accepted）かどうかを返します。

        Returns:
            bool: outputファイルコレクション内の判定結果が合格であれば True。
                  そもそもコレクションが存在しない（失敗時）場合は False。
        """
        if self.test_result_output_file_collection is None:
            return False
        return self.test_result_output_file_collection.is_accepted
