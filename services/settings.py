from domain.models.settings import GlobalSettings
from files.repositories.global_settings import GlobalSettingsRepository


class GlobalSettingsEditService:
    def __init__(self, global_settings_io: GlobalSettingsRepository):
        self._global_settings_io = global_settings_io

    def get_settings(self) -> GlobalSettings:
        return self._global_settings_io.get()

    def set_settings(self, settings: GlobalSettings) -> None:
        self._global_settings_io.put(settings)
