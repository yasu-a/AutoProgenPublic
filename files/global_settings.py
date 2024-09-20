import json
from contextlib import contextmanager

from PyQt5.QtCore import QMutex

from domain.models.settings import GlobalSettings
from files.path_providers.global_ import GlobalPathProvider


class GlobalSettingsRepository:
    def __init__(self, global_path_provider: GlobalPathProvider):
        self._global_path_provider = global_path_provider

        self.__model: GlobalSettings | None = None
        self.__lock = QMutex()

    @contextmanager
    def _lock(self):
        self.__lock.lock()
        try:
            yield
        finally:
            self.__lock.unlock()

    def _get_model_unlocked(self) -> GlobalSettings:
        if self.__model is None:
            json_fullpath = self._global_path_provider.global_settings_json_fullpath()
            if not json_fullpath.exists():
                self.__model = GlobalSettings.create_default()
            else:
                with json_fullpath.open(mode="r", encoding="utf-8") as f:
                    self.__model = GlobalSettings.from_json(json.load(f))
        assert self.__model is not None
        return self.__model

    def _set_model_unlocked(self, model: GlobalSettings):
        self.__model = model
        json_fullpath = self._global_path_provider.global_settings_json_fullpath()
        with json_fullpath.open(mode="w", encoding="utf-8") as f:
            json.dump(
                self.__model.to_json(),
                f,
                indent=2,
                ensure_ascii=False,
            )

    def put(self, model: GlobalSettings) -> None:
        with self._lock():
            self._set_model_unlocked(model)

    def get(self) -> GlobalSettings:
        with self._lock():
            return self._get_model_unlocked()
