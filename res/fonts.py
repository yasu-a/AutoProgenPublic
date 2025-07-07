from PyQt5.QtGui import QFont


def get_font(
        *,
        monospace=False,
        small=False,
        large=False,
        very_large=False,
        bold=False,
        underline=False,
) -> QFont:
    assert int(small) + int(large) + int(very_large) <= 1, (small, large, very_large)
    size_name = "small" if small else "large" if large else "very_large" if very_large else "normal"
    if monospace:
        size = {
            "small": 9,
            "normal": 10,
            "large": 13,
            "very_large": 16,
        }[size_name]
        name = "Consolas"
    else:
        size = {
            "small": 8,
            "normal": 9,
            "large": 12,
            "very_large": 15,
        }[size_name]
        name = "Meiryo"
    f = QFont(name, size)
    f.setBold(bold)
    f.setUnderline(underline)
    return f
