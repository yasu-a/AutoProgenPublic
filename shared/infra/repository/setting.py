from contextlib import contextmanager
from pathlib import Path

from PyQt5.QtCore import QMutex

from shared.domain.value.setting import Setting
from shared.infra.system.global_core_io import GlobalCoreIO


class SettingRepository:
    def __init__(
            self,
            *,
            settings_json_fullpath: Path,
            global_core_io: GlobalCoreIO,
    ):
        """
        Args:
            settings_json_fullpath: 設定ファイルのJSONパス
            global_core_io: JSON読み書き用のIO
        """
        self._settings_json_fullpath = settings_json_fullpath
        self._global_core_io = global_core_io

        self.__model: Setting | None = None
        self.__lock = QMutex()

    @contextmanager
    def _lock(self):
        self.__lock.lock()
        try:
            yield
        finally:
            self.__lock.unlock()

    def _get_model_unlocked(self) -> Setting:
        if self.__model is None:
            if not self._settings_json_fullpath.exists():
                self.__model = Setting.create_default()
            else:
                self.__model = Setting.from_json(
                    self._global_core_io.read_json(
                        json_fullpath=self._settings_json_fullpath,
                    )
                )
        assert self.__model is not None
        return self.__model

    def _set_model_unlocked(self, model: Setting) -> None:
        self.__model = model
        self._global_core_io.write_json(
            json_fullpath=self._settings_json_fullpath,
            body=self.__model.to_json(),
        )

    def put(self, model: Setting) -> None:
        with self._lock():
            self._set_model_unlocked(model)

    def get(self) -> Setting:
        with self._lock():
            return self._get_model_unlocked()
