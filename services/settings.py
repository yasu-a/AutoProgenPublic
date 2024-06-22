from pathlib import Path

from files.settings import GlobalSettingsIO


class GlobalSettingsService:
    def __init__(self, global_settings_io: GlobalSettingsIO):
        self._global_settings_io = global_settings_io

    def get_compiler_tool_fullpath(self) -> Path | None:
        return self._global_settings_io.get_compiler_tool_fullpath()

    def set_compiler_tool_fullpath(self, fullpath: Path) -> None:
        self._global_settings_io.set_compiler_tool_fullpath(fullpath)

    def get_compiler_timeout(self) -> float:
        return self._global_settings_io.get_compiler_timeout()

    def set_compiler_timeout(self, timeout: float) -> None:
        self._global_settings_io.set_compiler_timeout(timeout)

    def get_max_workers(self) -> int:
        return self._global_settings_io.get_max_workers()

    def set_max_workers(self, max_workers: int) -> None:
        self._global_settings_io.set_max_workers(max_workers)
