from domain.models.global_settings import GlobalSettings
from services.global_settings import GlobalSettingsGetService, GlobalSettingsPutService


class GlobalSettingsGetUseCase:
    def __init__(
            self,
            *,
            global_settings_get_service: GlobalSettingsGetService,
    ):
        self._global_settings_get_service = global_settings_get_service

    def execute(self) -> GlobalSettings:
        return self._global_settings_get_service.execute()


class GlobalSettingsPutUseCase:
    def __init__(
            self,
            *,
            global_settings_put_service: GlobalSettingsPutService,
    ):
        self._global_settings_put_service = global_settings_put_service

    def execute(self, global_settings: GlobalSettings) -> None:
        self._global_settings_put_service.execute(global_settings)
