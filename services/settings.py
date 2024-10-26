from domain.models.settings import GlobalConfig
from files.repositories.global_config import GlobalConfigRepository


class GlobalSettingsEditService:
    def __init__(self, global_settings_io: GlobalConfigRepository):
        self._global_settings_io = global_settings_io

    def get_settings(self) -> GlobalConfig:
        return self._global_settings_io.get()

    def set_settings(self, settings: GlobalConfig) -> None:
        self._global_settings_io.put(settings)
