from domain.model.global_settings import GlobalSettings
from infra.repository.global_settings import GlobalSettingsRepository


class GlobalSettingsGetUseCase:
    def __init__(
            self,
            *,
            global_settings_repo: GlobalSettingsRepository,
    ):
        self._global_settings_repo = global_settings_repo

    def execute(self) -> GlobalSettings:
        return self._global_settings_repo.get()


class GlobalSettingsPutUseCase:
    def __init__(
            self,
            *,
            global_settings_repo: GlobalSettingsRepository,
    ):
        self._global_settings_repo = global_settings_repo

    def execute(self, global_settings: GlobalSettings) -> None:
        self._global_settings_repo.put(global_settings)
