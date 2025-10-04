from contextlib import contextmanager

from PyQt5.QtCore import QMutex

from domain.model.global_settings import GlobalSettings
from infra.io.files.global_ import GlobalCoreIO
from infra.path_provider.global_ import GlobalPathProvider


class GlobalSettingsRepository:
    def __init__(
            self,
            *,
            global_core_io: GlobalCoreIO,
            global_path_provider: GlobalPathProvider,
    ):
        self._global_core_io = global_core_io
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
                self.__model = GlobalSettings.from_json(
                    self._global_core_io.read_json(
                        json_fullpath=json_fullpath,
                    )
                )
        assert self.__model is not None
        return self.__model

    def _set_model_unlocked(self, model: GlobalSettings) -> None:
        self.__model = model
        json_fullpath = self._global_path_provider.global_settings_json_fullpath()
        self._global_core_io.write_json(
            json_fullpath=json_fullpath,
            body=self.__model.to_json(),
        )

    def put(self, model: GlobalSettings) -> None:
        with self._lock():
            self._set_model_unlocked(model)

    def get(self) -> GlobalSettings:
        with self._lock():
            return self._get_model_unlocked()
