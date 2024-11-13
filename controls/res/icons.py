from functools import cache

from PyQt5.QtGui import QIcon, QPixmap, QTransform

from application.dependency.path_provider import get_global_base_path

__all__ = "get_icon",


@cache
def _get_pixmap(filename: str) -> QPixmap:
    filepath = str(get_global_base_path() / "img" / f"{filename}.png")
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
