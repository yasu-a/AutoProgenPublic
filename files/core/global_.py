import json
from pathlib import Path
from typing import Optional


class GlobalCoreIO:
    def __init__(self):
        pass

    # noinspection PyMethodMayBeStatic
    def read_json(
            self,
            *,
            json_fullpath: Path,
    ) -> Optional:
        with json_fullpath.open(mode="r", encoding="utf-8") as f:
            return json.load(f)

    # noinspection PyMethodMayBeStatic
    def read_file_content_str(
            self,
            *,
            file_fullpath: Path,
    ) -> str:
        with file_fullpath.open(mode="r", encoding="utf-8") as f:
            return f.read()

    # noinspection PyMethodMayBeStatic
    def read_file_content_bytes(
            self,
            *,
            file_fullpath: Path,
    ) -> bytes:
        with file_fullpath.open(mode="rb") as f:
            return f.read()
