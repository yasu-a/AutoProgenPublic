from autoprogen.domain.model.project_settings import ProjectSettings
from autoprogen.domain.model.value import StudentID
from autoprogen.infra.repository.project_settings import ProjectSettingsRepository
from autoprogen.service.student_change_event_bus import StudentChangeEventBus
from autoprogen.usecase.student_mark import StudentMarkGetUseCase


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
