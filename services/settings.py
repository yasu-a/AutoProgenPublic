from domain.models.settings import GlobalSettings
from files.settings import GlobalSettingsIO


class GlobalSettingsEditService:
    def __init__(self, global_settings_io: GlobalSettingsIO):
        self._global_settings_io = global_settings_io

    def get_settings(self) -> GlobalSettings:
        return self._global_settings_io.get_settings()

    def set_settings(self, settings: GlobalSettings) -> None:
        self._global_settings_io.set_settings(settings)
