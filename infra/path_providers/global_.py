from pathlib import Path


class GlobalPathProvider:
    def __init__(self, global_settings_folder_fullpath: Path):
        self._base = global_settings_folder_fullpath

    def global_settings_json_fullpath(self) -> Path:
        return self._base / "settings.json"

    def test_source_file_fullpath(self) -> Path:
        return self._base / "vctest" / "test.c"
