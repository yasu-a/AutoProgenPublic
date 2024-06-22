import json
from contextlib import contextmanager
from pathlib import Path

from PyQt5.QtCore import QMutex

from models.settings import GlobalSettings


class GlobalPathProvider:
    def __init__(self, global_settings_folder_fullpath: Path):
        self._base = global_settings_folder_fullpath

    def global_settings_json_fullpath(self) -> Path:
        return self._base / "settings.json"


class GlobalSettingsIO:
    def __init__(self, global_path_provider: GlobalPathProvider):
        self._global_path_provider = global_path_provider

        self.__current_modify_count = 0
        self.__model: GlobalSettings | None = None
        self.__modify_count_on_load = -1
        self.__lock = QMutex()

    @contextmanager
    def _lock(self):
        self.__lock.lock()
        try:
            yield
        finally:
            self.__lock.unlock()

    def _get_model(self) -> GlobalSettings:
        if self.__model is None or self.__modify_count_on_load != self.__current_modify_count:
            json_fullpath = self._global_path_provider.global_settings_json_fullpath()
            if not json_fullpath.exists():
                self.__model = GlobalSettings.create_default()
            else:
                with json_fullpath.open(mode="r", encoding="utf-8") as f:
                    self.__model = GlobalSettings.from_json(json.load(f))
            self.__modify_count_on_load = self.__current_modify_count
        assert self.__model is not None
        return self.__model

    def _save_model(self) -> None:
        json_fullpath = self._global_path_provider.global_settings_json_fullpath()
        with json_fullpath.open(mode="w", encoding="utf-8") as f:
            json.dump(
                self.__model.to_json(),
                f,
                indent=2,
                ensure_ascii=False,
            )
        self.__current_modify_count += 1

    def get_compiler_tool_fullpath(self) -> Path | None:
        with self._lock():
            return self._get_model().compiler_tool_fullpath

    def set_compiler_tool_fullpath(self, fullpath: Path) -> None:
        with self._lock():
            self._get_model().compiler_tool_fullpath = fullpath
            self._save_model()

    def get_compiler_timeout(self) -> float:
        with self._lock():
            return self._get_model().compiler_timeout

    def set_compiler_timeout(self, compiler_timeout: float) -> None:
        with self._lock():
            self._get_model().compiler_timeout = compiler_timeout
            self._save_model()

    def get_max_workers(self) -> int:
        with self._lock():
            return self._get_model().max_workers

    def set_max_workers(self, max_workers: int) -> None:
        with self._lock():
            self._get_model().max_workers = max_workers
            self._save_model()
