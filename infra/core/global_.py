import json
from pathlib import Path
from typing import Optional, Any

from app_logging import create_logger


class GlobalCoreIO:
    _logger = create_logger()

    def __init__(self):
        pass

    # noinspection PyMethodMayBeStatic
    def read_json(
            self,
            *,
            json_fullpath: Path,
    ) -> Optional:
        self._logger.debug(f"read_json({json_fullpath=})")
        with json_fullpath.open(mode="r", encoding="utf-8") as f:
            return json.load(f)

    # noinspection PyMethodMayBeStatic
    def write_json(
            self,
            *,
            json_fullpath: Path,
            body: Any,
    ):
        self._logger.debug(f"write_json({json_fullpath=})")
        json_fullpath.parent.mkdir(parents=True, exist_ok=True)
        with json_fullpath.open(mode="w", encoding="utf-8") as f:
            json.dump(
                body,
                f,
                indent=2,
                ensure_ascii=False,
            )

    # noinspection PyMethodMayBeStatic
    def read_file_content_str(
            self,
            *,
            file_fullpath: Path,
    ) -> str:
        self._logger.debug(f"read_file_content_str({file_fullpath=})")
        with file_fullpath.open(mode="r", encoding="utf-8") as f:
            return f.read()

    # noinspection PyMethodMayBeStatic
    def read_file_content_bytes(
            self,
            *,
            file_fullpath: Path,
    ) -> bytes:
        self._logger.debug(f"read_file_content_bytes({file_fullpath=})")
        with file_fullpath.open(mode="rb") as f:
            return f.read()
