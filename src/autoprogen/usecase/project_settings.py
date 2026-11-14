from autoprogen.domain.model.project_settings import ProjectSettings
from autoprogen.infra.repository.project_settings import ProjectSettingsRepository


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

    def __init__(self, *, project_settings_repo: ProjectSettingsRepository) -> None:
        """保存先Repositoryを受け取る。"""
        self._project_settings_repo = project_settings_repo

    def execute(self, settings: ProjectSettings) -> None:
        """プロジェクト設定を保存する。"""
        self._project_settings_repo.put(settings)
