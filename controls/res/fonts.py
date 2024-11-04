from PyQt5.QtGui import QFont


def font(monospace=False, small=False, bold=False, large=False) -> QFont:
    assert not (small is True and large is True), (small, large)
    if monospace:
        f = QFont("Consolas", 9 if small else (13 if large else 10))
    else:
        f = QFont("Meiryo", 8 if small else (12 if large else 9))
    f.setBold(bold)
    return f
