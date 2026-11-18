from autoprogen.domain.error.stage.build import SubmissionNotFoundError
from autoprogen.domain.model.project_settings import ProjectSettings
from autoprogen.domain.model.student_mark import StudentMark
from autoprogen.domain.model.value import StudentID
from autoprogen.infra.repository.project_settings import ProjectSettingsRepository
from autoprogen.infra.repository.student_stage_path_result import (
    StudentStagePathResultRepository,
)
from autoprogen.infra.task.manager import TaskManager
from autoprogen.service.stage_path import StagePathListSubService
from autoprogen.service.student_change_event_bus import StudentChangeEventBus
from autoprogen.usecase.student_mark import StudentMarkGetUseCase, StudentMarkPutUseCase


class ProjectSettingsGetUseCase:
    """現在のプロジェクトの設定を取得する。"""

    def __init__(self, *, project_settings_repo: ProjectSettingsRepository) -> None:
        """保存先Repositoryを受け取る。"""
        self._project_settings_repo = project_settings_repo

    def execute(self) -> ProjectSettings:
        """プロジェクト設定を読み込む。"""
        return self._project_settings_repo.get()


class ProjectSettingsPutUseCase:
    """現在のプロジェクトの設定を保存する。"""

    def __init__(
            self,
            *,
            project_settings_repo: ProjectSettingsRepository,
            student_change_event_bus: StudentChangeEventBus,
    ) -> None:
        """保存先Repositoryと学生変更の通知先を受け取る。"""
        self._project_settings_repo = project_settings_repo
        self._student_change_event_bus = student_change_event_bus

    def execute(self, settings: ProjectSettings) -> None:
        """設定を保存し、採点除外が変化した学生だけを通知する。"""
        previous = self._project_settings_repo.get()
        self._project_settings_repo.put(settings)
        changed_student_ids = (
            previous.bulk_grading_skips ^ settings.bulk_grading_skips
        )
        for student_id in sorted(changed_student_ids, key=str):
            self._student_change_event_bus.notify(student_id)


class BulkGradingSkipAddUseCaseError(ValueError):
    """未採点の学生を一括採点の除外対象へ追加しようとした場合のエラー。"""


class BulkGradingSkipAddUseCase:
    """採点済みの学生をプロジェクトの一括採点除外へ追加する。"""

    def __init__(
            self,
            *,
            student_mark_get_usecase: StudentMarkGetUseCase,
            project_settings_get_usecase: ProjectSettingsGetUseCase,
            project_settings_put_usecase: ProjectSettingsPutUseCase,
    ) -> None:
        """点数と設定の取得・保存経路を受け取る。"""
        self._student_mark_get_usecase = student_mark_get_usecase
        self._project_settings_get_usecase = project_settings_get_usecase
        self._project_settings_put_usecase = project_settings_put_usecase

    def execute(self, student_id: StudentID) -> None:
        """点数がある学生だけを一括採点の除外対象へ追加する。"""
        student_mark = self._student_mark_get_usecase.execute(student_id)
        if student_mark.score is None:
            raise BulkGradingSkipAddUseCaseError(
                "未採点の学生は一括採点の除外対象へ追加できません"
            )
        settings = self._project_settings_get_usecase.execute()
        self._project_settings_put_usecase.execute(
            settings.with_bulk_grading_skip(student_id)
        )


class NotSubmittedStudentExcludeUseCaseError(RuntimeError):
    """未提出学生の0点保存または除外登録を完了できなかった場合のエラー。"""

    def __init__(self, message: str, *, score_saved: bool = False) -> None:
        """利用者へ部分保存の有無を伝えられるよう状態を保持する。"""
        super().__init__(message)
        self.score_saved = score_saved


class NotSubmittedStudentExcludeUseCase:
    """構造化された未提出エラーを再確認し、0点保存後に採点除外へ追加する。"""

    def __init__(
            self,
            *,
            stage_path_list_sub_service: StagePathListSubService,
            student_stage_path_result_repository: StudentStagePathResultRepository,
            student_mark_put_usecase: StudentMarkPutUseCase,
            bulk_grading_skip_add_usecase: BulkGradingSkipAddUseCase,
            project_settings_get_usecase: ProjectSettingsGetUseCase,
            task_manager: TaskManager,
    ) -> None:
        """最新結果、点数、設定、実行状態を扱う既存経路を受け取る。"""
        self._stage_path_list_sub_service = stage_path_list_sub_service
        self._student_stage_path_result_repository = (
            student_stage_path_result_repository
        )
        self._student_mark_put_usecase = student_mark_put_usecase
        self._bulk_grading_skip_add_usecase = bulk_grading_skip_add_usecase
        self._project_settings_get_usecase = project_settings_get_usecase
        self._task_manager = task_manager

    def _has_not_submitted_error(self, student_id: StudentID) -> bool:
        """最新のステージ結果に構造化された未提出エラーがあるか返す。"""
        for stage_path in self._stage_path_list_sub_service.execute():
            result = self._student_stage_path_result_repository.get(
                student_id,
                stage_path,
            )
            last_result = result.last_stage_result
            if (
                    last_result is not None
                    and isinstance(last_result.error, SubmissionNotFoundError)
            ):
                return True
        return False

    def execute(self, student_id: StudentID) -> None:
        """未提出状態を検査し、0点保存後に一括採点除外へ追加する。"""
        if not self._task_manager.is_empty():
            raise NotSubmittedStudentExcludeUseCaseError(
                "実行中は未提出学生への処置を行えません"
            )
        if not self._has_not_submitted_error(student_id):
            raise NotSubmittedStudentExcludeUseCaseError(
                "未提出エラーが解消されています。表示を更新してください"
            )
        settings = self._project_settings_get_usecase.execute()
        if student_id in settings.bulk_grading_skips:
            raise NotSubmittedStudentExcludeUseCaseError(
                "この学生はすでに一括採点から除外されています"
            )
        if not self._task_manager.is_empty():
            raise NotSubmittedStudentExcludeUseCaseError(
                "実行が開始されたため未提出学生への処置を中止しました"
            )

        # 最新状態を確認した直後に、既存の点数保存経路で0点を確定する。
        try:
            self._student_mark_put_usecase.execute(StudentMark(student_id, 0))
        except Exception as error:
            raise NotSubmittedStudentExcludeUseCaseError(
                f"0点を保存できませんでした。\n{error}"
            ) from error

        # 点数保存後に処理が始まった場合は、設定を変更せず部分保存を明示する。
        if not self._task_manager.is_empty():
            raise NotSubmittedStudentExcludeUseCaseError(
                "0点は保存されましたが、実行が開始されたため除外設定は保存していません",
                score_saved=True,
            )
        try:
            self._bulk_grading_skip_add_usecase.execute(student_id)
        except Exception as error:
            raise NotSubmittedStudentExcludeUseCaseError(
                f"0点は保存されましたが、除外設定を保存できませんでした。\n{error}",
                score_saved=True,
            ) from error
