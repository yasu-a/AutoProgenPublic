import os.path

from PyQt5.QtGui import QIcon


def icon(filename):
    return QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"img/{filename}.png"))
