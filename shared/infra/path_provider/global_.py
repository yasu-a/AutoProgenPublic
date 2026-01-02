from pathlib import Path


class GlobalPathProvider:
    def __init__(self, settings_folder_fullpath: Path):
        self._base = settings_folder_fullpath

    def settings_json_fullpath(self) -> Path:
        return self._base / "settings.json"

    def test_source_file_fullpath(self) -> Path:
        return self._base / "vctest" / "test.c"

    def app_version_json_fullpath(self) -> Path:
        return self._base / "app_version.json"
