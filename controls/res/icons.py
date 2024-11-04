from PyQt5.QtGui import QIcon

from application.dependency.path_provider import get_global_base_path

__all__ = "icon",


def icon(filename):
    return QIcon(str(get_global_base_path() / "img" / f"{filename}.png"))
