import json
from contextlib import contextmanager
from pathlib import Path

from PyQt5.QtCore import QMutex

from domain.models.settings import GlobalSettings
from files.global_path_provider import GlobalPathProvider


class GlobalSettingsIO:
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

    def get_compiler_tool_fullpath(self) -> Path | None:
        with self._lock():
            return self._get_model_unlocked().compiler_tool_fullpath

    def get_compiler_timeout(self) -> float:
        with self._lock():
            return self._get_model_unlocked().compiler_timeout

    def get_max_workers(self) -> int:
        with self._lock():
            return self._get_model_unlocked().max_workers

    def get_settings(self) -> GlobalSettings:
        with self._lock():
            return self._get_model_unlocked()

    def set_settings(self, settings: GlobalSettings):
        with self._lock():
            self._set_model_unlocked(settings)
