from autoprogen.domain.error.stage.compile import SourceSafetyViolationError
from autoprogen.domain.model.project_settings import SourceCodeCheckSkip
from autoprogen.domain.model.value import StudentID
from autoprogen.infra.repository.student_stage_path_result import (
    StudentStagePathResultRepository,
)
from autoprogen.infra.task.manager import TaskManager
from autoprogen.service.stage_path import StagePathListSubService
from autoprogen.usecase.project_settings import (
    ProjectSettingsGetUseCase,
    ProjectSettingsPutUseCase,
)
from autoprogen.usecase.student_source_code import StudentSourceCodeGetUseCase


class SourceCodeCheckSkipApproveUseCaseError(RuntimeError):
    """安全性チェックの許可を現在の状態では実行できないことを表す。"""


class SourceCodeCheckSkipApproveUseCase:
    """現在の学生の検査対象ソースだけを安全性チェック省略へ登録する。"""

    def __init__(
            self,
            *,
            student_source_code_get_usecase: StudentSourceCodeGetUseCase,
            stage_path_list_sub_service: StagePathListSubService,
            student_stage_path_result_repository: StudentStagePathResultRepository,
            project_settings_get_usecase: ProjectSettingsGetUseCase,
            project_settings_put_usecase: ProjectSettingsPutUseCase,
            task_manager: TaskManager,
    ) -> None:
        """現在のソース、実行結果、設定および実行状態の取得経路を受け取る。"""
        self._student_source_code_get_usecase = student_source_code_get_usecase
        self._stage_path_list_sub_service = stage_path_list_sub_service
        self._student_stage_path_result_repository = (
            student_stage_path_result_repository
        )
        self._project_settings_get_usecase = project_settings_get_usecase
        self._project_settings_put_usecase = project_settings_put_usecase
        self._task_manager = task_manager

    def _has_matching_safety_error(
            self,
            *,
            student_id: StudentID,
            expected_sha256: str,
    ) -> bool:
        """最新のステージ結果に同じソースの安全性チェックエラーがあるか返す。"""
        for stage_path in self._stage_path_list_sub_service.execute():
            result = self._student_stage_path_result_repository.get(
                student_id,
                stage_path,
            )
            last_result = result.last_stage_result
            if (
                    last_result is not None
                    and isinstance(last_result.error, SourceSafetyViolationError)
                    and last_result.error.source_sha256 == expected_sha256
            ):
                return True
        return False

    def execute(self, *, student_id: StudentID, expected_sha256: str) -> None:
        """現在の状態を再検証したあと許可設定を保存する。"""
        # Value Objectの生成によって、学籍番号とSHA-256の保存形式を検証する。
        try:
            skip = SourceCodeCheckSkip(student_id, expected_sha256)
        except (TypeError, ValueError) as error:
            raise SourceCodeCheckSkipApproveUseCaseError(
                "検査対象の学生またはSHA-256を特定できないため許可できません。"
            ) from error
        if not self._task_manager.is_empty():
            raise SourceCodeCheckSkipApproveUseCaseError(
                "実行中はソースコードを許可できません。実行完了後に開き直してください。"
            )

        try:
            source_code = self._student_source_code_get_usecase.execute(student_id)
        except (FileNotFoundError, UnicodeError) as error:
            raise SourceCodeCheckSkipApproveUseCaseError(
                "ソースコードを取得できないため許可できません。"
            ) from error
        if source_code is None:
            raise SourceCodeCheckSkipApproveUseCaseError(
                "ソースコードを取得できないため許可できません。"
            )
        if source_code.calculate_sha256() != expected_sha256:
            raise SourceCodeCheckSkipApproveUseCaseError(
                "ソースコードが更新されました。再実行してから許可してください。"
            )
        if not self._has_matching_safety_error(
                student_id=student_id,
                expected_sha256=expected_sha256,
        ):
            raise SourceCodeCheckSkipApproveUseCaseError(
                "安全性チェックエラーが更新されました。表示を更新してください。"
            )

        settings = self._project_settings_get_usecase.execute()
        if skip in settings.source_code_check_skips:
            return
        if not self._task_manager.is_empty():
            raise SourceCodeCheckSkipApproveUseCaseError(
                "実行が開始されたためソースコードの許可を中止しました。"
            )
        self._project_settings_put_usecase.execute(
            settings.with_source_code_check_skip(
                student_id=student_id,
                source_sha256=expected_sha256,
            )
        )
