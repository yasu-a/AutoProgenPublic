from contextlib import contextmanager
from pathlib import Path

from PyQt5.QtCore import QMutex

from shared.domain.interface.repository import ISettingRepository
from shared.domain.interface.system import IGlobalCoreIO
from shared.domain.value.setting import Setting


class SettingRepository(ISettingRepository):
    def __init__(
            self,
            *,
            setting_json_path: Path,
            global_core_io: IGlobalCoreIO,
    ):
        """
        Args:
            setting_json_path: 設定ファイルのJSONパス
            global_core_io: JSON読み書き用のIO
        """
        self._setting_json_path = setting_json_path
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
            if not self._setting_json_path.exists():
                self.__model = Setting.create_default()
            else:
                self.__model = Setting.from_json(
                    self._global_core_io.read_json(
                        json_fullpath=self._setting_json_path,
                    )
                )
        assert self.__model is not None
        return self.__model

    def _set_model_unlocked(self, model: Setting) -> None:
        self.__model = model
        self._global_core_io.write_json(
            json_fullpath=self._setting_json_path,
            body=self.__model.to_json(),
        )

    def put(self, model: Setting) -> None:
        with self._lock():
            self._set_model_unlocked(model)

    def get(self) -> Setting:
        with self._lock():
            return self._get_model_unlocked()
