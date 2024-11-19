from domain.models.global_settings import GlobalSettings
from infra.repositories.global_settings import GlobalSettingsRepository


class GlobalSettingsGetService:
    def __init__(
            self,
            *,
            global_settings_repo: GlobalSettingsRepository,
    ):
        self._global_settings_repo = global_settings_repo

    def execute(self) -> GlobalSettings:
        return self._global_settings_repo.get()


class GlobalSettingsPutService:
    def __init__(
            self,
            *,
            global_settings_repo: GlobalSettingsRepository,
    ):
        self._global_settings_repo = global_settings_repo

    def execute(self, global_settings: GlobalSettings) -> None:
        self._global_settings_repo.put(global_settings)
