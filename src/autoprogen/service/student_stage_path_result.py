from datetime import datetime

from autoprogen.service.student_change_event_bus import StudentChangeEventBus
from autoprogen.domain.model.stage_path import StagePath
from autoprogen.domain.model.project_settings import SourceCodeCheckSkip
from autoprogen.domain.model.stage import AbstractStage, BuildStage, CompileStage, ExecuteStage, TestStage
from autoprogen.domain.model.student_stage_path_result import StudentStagePathResult
from autoprogen.domain.model.student_stage_result import BuildStudentStageResult, \
    CompileStudentStageResult, ExecuteStudentStageResult, \
    TestStudentStageResult, AbstractStudentStageResult
from autoprogen.domain.model.value import StudentID
from autoprogen.infra.repository.project_settings import ProjectSettingsRepository
from autoprogen.infra.repository.student_stage_path_result import StudentStagePathResultRepository
from autoprogen.service.stage_path import StagePathListSubService
from autoprogen.service.student_dynamic import StudentDynamicGetSourceCodeService
from autoprogen.service.student_submission import StudentSubmissionGetChecksumService
from autoprogen.service.testcase_config import TestCaseConfigGetExecuteConfigMtimeService, \
    TestCaseConfigGetTestConfigMtimeService


class StudentStagePathResultGetService:
    # 生徒の指定されたステージパスの各ステージの結果を取得する
    # テーブル表示におけるHOTSPOT

    def __init__(
            self,
            *,
            student_stage_path_result_repo: StudentStagePathResultRepository,
    ):
        self._student_stage_path_result_repo = student_stage_path_result_repo

    def execute(self, student_id: StudentID, stage_path: StagePath) \
            -> StudentStagePathResult | None:
        return self._student_stage_path_result_repo.get(student_id, stage_path)


class StudentStagePathResultCheckOutdatedService:
    """保存済みステージ結果が現在の実行条件に対して古いか判定する。"""

    def __init__(
            self,
            student_submission_get_checksum_service: StudentSubmissionGetChecksumService,
            project_settings_repository: ProjectSettingsRepository,
            student_dynamic_get_source_code_service: StudentDynamicGetSourceCodeService,
            testcase_config_get_execute_config_mtime_service: TestCaseConfigGetExecuteConfigMtimeService,
            testcase_config_get_test_config_mtime_service: TestCaseConfigGetTestConfigMtimeService,
    ):
        """現在の実行条件を取得する既存サービスとRepositoryを受け取る。"""
        self._student_submission_get_checksum_service \
            = student_submission_get_checksum_service
        self._project_settings_repository = project_settings_repository
        self._student_dynamic_get_source_code_service \
            = student_dynamic_get_source_code_service
        self._testcase_config_get_execute_config_mtime_service \
            = testcase_config_get_execute_config_mtime_service
        self._testcase_config_get_test_config_mtime_service \
            = testcase_config_get_test_config_mtime_service

    def execute(
            self,
            *,
            stage_path_result: StudentStagePathResult,
            student_id: StudentID,
    ) -> type[AbstractStage] | None:
        """Outdatedを検出した最初のステージを返し、なければNoneを返す。"""
        # BUILD結果が存在する場合は提出内容の変更を確認する。
        result = stage_path_result.get_result_by_stage_type(BuildStage)
        if result is not None:
            assert isinstance(result, BuildStudentStageResult)
            # 保存時と現在の提出フォルダのチェックサムを比較する。
            checksum = self._student_submission_get_checksum_service.execute(
                student_id=student_id,
            )
            if result.is_outdated(
                current_submission_folder_checksum=checksum,
            ):
                return BuildStage

        # COMPILE結果が存在する場合は安全性チェック設定の変更を確認する。
        result = stage_path_result.get_result_by_stage_type(CompileStage)
        if result is not None:
            assert isinstance(result, CompileStudentStageResult)
            # 現在のプロジェクト設定を一度だけ取得する。
            project_settings = self._project_settings_repository.get()
            # 同じ学生とソースコードに対する省略許可の有無を比較する。
            try:
                source_code = self._student_dynamic_get_source_code_service.execute(
                    student_id,
                )
            except FileNotFoundError:
                # BUILD成果物が欠損している場合はソースコードを再生成する。
                return BuildStage
            current_skip = SourceCodeCheckSkip(
                student_id=student_id,
                source_sha256=source_code.calculate_sha256(),
            )
            is_source_code_check_skipped = (
                current_skip in project_settings.source_code_check_skips
            )
            if result.is_outdated(
                current_suppressed_source_code_checks=(
                    project_settings.suppressed_source_code_checks
                ),
                current_source_code_check_skipped=is_source_code_check_skipped,
            ):
                return CompileStage

        # EXECUTE結果が存在する場合は実行設定の変更を確認する。
        # noinspection DuplicatedCode
        result = stage_path_result.get_result_by_stage_type(ExecuteStage)
        if result is not None:
            assert isinstance(result, ExecuteStudentStageResult)
            # 保存時と現在の実行構成の更新時刻を比較する。
            stage = result.stage
            assert isinstance(stage, ExecuteStage)
            mtime = self._testcase_config_get_execute_config_mtime_service.execute(
                testcase_id=stage.testcase_id,
            )
            if result.is_outdated(current_execute_config_mtime=mtime):
                return ExecuteStage

        # TEST結果が存在する場合はテスト設定の変更を確認する。
        # noinspection DuplicatedCode
        result = stage_path_result.get_result_by_stage_type(TestStage)
        if result is not None:
            assert isinstance(result, TestStudentStageResult)
            # 保存時と現在のテスト構成の更新時刻を比較する。
            stage = result.stage
            assert isinstance(stage, TestStage)
            mtime = self._testcase_config_get_test_config_mtime_service.execute(
                testcase_id=stage.testcase_id,
            )
            if result.is_outdated(current_test_config_mtime=mtime):
                return TestStage

        return None


class StudentStageResultCheckTimestampQueryService:
    # 生徒の進捗データの最終更新日時を取得する

    def __init__(
            self,
            *,
            student_stage_path_result_repo: StudentStagePathResultRepository,
    ):
        self._student_stage_path_result_repo = student_stage_path_result_repo

    def execute(self, student_id: StudentID) -> datetime | None:  # None if no file exists
        return self._student_stage_path_result_repo.get_timestamp(student_id)


class StudentStagePathResultPutService:
    """ステージ結果の保存に成功した後、対象学生の変更を通知する。"""

    def __init__(
            self,
            *,
            student_stage_path_result_repo: StudentStagePathResultRepository,
            student_change_event_bus: StudentChangeEventBus,
    ) -> None:
        """保存先とプロジェクト単位の通知先を受け取る。"""
        self._student_stage_path_result_repo = student_stage_path_result_repo
        self._student_change_event_bus = student_change_event_bus

    def execute(self, stage_path_result: StudentStagePathResult) -> None:
        """ステージ結果を保存し、成功した場合だけ変更を通知する。"""
        self._student_stage_path_result_repo.put(stage_path_result)
        self._student_change_event_bus.notify(stage_path_result.student_id)


class StudentStageResultClearService:
    """学生のステージ結果をすべて削除する。"""

    def __init__(
            self,
            *,
            stage_path_list_sub_service: StagePathListSubService,
            student_stage_path_result_repo: StudentStagePathResultRepository,
            student_stage_path_result_put_service: StudentStagePathResultPutService,
    ):
        """ステージ一覧、読み込み先、共通保存サービスを受け取る。"""
        self._stage_path_list_sub_service = stage_path_list_sub_service
        self._student_stage_path_result_repo = student_stage_path_result_repo
        self._student_stage_path_result_put_service = student_stage_path_result_put_service

    def execute(
            self,
            *,
            student_id: StudentID,
    ) -> None:
        """対象学生の各ステージ結果を削除して保存する。"""
        stage_paths = self._stage_path_list_sub_service.execute()
        for stage_path in stage_paths:
            stage_path_result = self._student_stage_path_result_repo.get(
                student_id, stage_path)
            stage_path_result.delete_all_results()
            self._student_stage_path_result_put_service.execute(
                stage_path_result)


class StudentPutStageResultService:
    """単一ステージの結果を既存のステージパス結果へ反映する。"""

    def __init__(
            self,
            *,
            student_stage_path_result_repo: StudentStagePathResultRepository,
            student_stage_path_result_put_service: StudentStagePathResultPutService,
    ):
        """読み込み先と共通保存サービスを受け取る。"""
        self._student_stage_path_result_repo = student_stage_path_result_repo
        self._student_stage_path_result_put_service = student_stage_path_result_put_service

    def execute(self, stage_path: StagePath, result: AbstractStudentStageResult) -> None:
        """単一ステージの結果を反映し、共通サービス経由で保存する。"""
        stage_path_result = self._student_stage_path_result_repo.get(
            student_id=result.student_id,
            stage_path=stage_path,
        )
        stage_path_result.put_result(result)
        self._student_stage_path_result_put_service.execute(stage_path_result)


class StudentGetStageResultService:
    def __init__(
            self,
            *,
            student_stage_path_result_repo: StudentStagePathResultRepository,
    ):
        self._student_stage_path_result_repo = student_stage_path_result_repo

    def execute(self, student_id: StudentID, stage_path: StagePath,
                stage: AbstractStage) -> AbstractStudentStageResult:
        stage_path_result = self._student_stage_path_result_repo.get(
            student_id=student_id,
            stage_path=stage_path,
        )
        return stage_path_result.get_result(stage)
