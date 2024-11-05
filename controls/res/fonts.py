from PyQt5.QtGui import QFont


def font(
        *,
        monospace=False,
        small=False,
        bold=False,
        large=False,
        very_large=False,
        underline=False,
) -> QFont:
    assert int(small) + int(large) + int(very_large) <= 1, (small, large, very_large)
    if monospace:
        f = QFont("Consolas", 9 if small else (13 if large else (16 if very_large else 10)))
    else:
        f = QFont("Meiryo", 8 if small else (12 if large else (15 if very_large else 9)))
    f.setBold(bold)
    f.setUnderline(underline)
    return f
