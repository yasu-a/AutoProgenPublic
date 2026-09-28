from functools import cache
from pathlib import Path

from PyQt5.QtGui import QIcon, QPixmap, QTransform

from autoprogen.app_path import get_app_base_dir

__all__ = "get_icon",


def _get_icon_fullpath(filename: str) -> Path:
    return get_app_base_dir() / "static" / "icon" / f"{filename}.png"


@cache
def _get_pixmap(filename: str) -> QPixmap:
    filepath = str(_get_icon_fullpath(filename))
    pixmap = QPixmap(filepath)
    if pixmap.isNull():
        raise FileNotFoundError(f"Icon '{filename}' not found.")
    return pixmap


def get_icon(filename, *, rotate: float = None) -> QIcon:
    pixmap = _get_pixmap(filename)

    if rotate is not None:
        trans = QTransform()
        trans.rotate(rotate)
        pixmap = pixmap.transformed(trans)

    return QIcon(pixmap)
