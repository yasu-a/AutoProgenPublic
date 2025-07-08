from PyQt5.QtWidgets import QDialog, QGridLayout, QVBoxLayout, QLabel, QHBoxLayout

from res.fonts import get_font


class MarkHelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    _SHORTCUTS = [
        ("前の生徒", ["A", "Left"]),
        ("次の生徒", ["D", "Right"]),
        ("前のテストケース", ["Q"]),
        ("次のテストケース", ["E"]),
        ("前のストリーム", ["Z"]),
        ("次のストリーム", ["C"]),
        ("点数のクリア", ["Space", "Delete"])
    ]

    def _init_ui(self):
        self.setModal(True)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self._l_title = QLabel(self)
        self._l_title.setFont(get_font(bold=True))
        self._l_title.setText("採点画面ショートカット一覧")
        layout.addWidget(self._l_title)

        layout_shortcut = QGridLayout()
        layout_shortcut.setSpacing(10)
        layout.addLayout(layout_shortcut)

        for i, (shortcut_role, shortcut_keys) in enumerate(self._SHORTCUTS):
            label = QLabel(shortcut_role, self)
            label.setFont(get_font(small=True))
            layout_shortcut.addWidget(label, i, 0)

            label = QLabel(" ", self)
            layout_shortcut.addWidget(label, i, 1)

            layout_cell = QHBoxLayout()
            layout_cell.setContentsMargins(0, 0, 0, 0)
            layout_shortcut.addLayout(layout_cell, i, 2)

            for j, shortcut_key in enumerate(shortcut_keys):
                label = QLabel(shortcut_key, self)
                label.setStyleSheet(
                    "color: white;"
                    "background-color: #0033aa;"
                    "border-radius: 4px;"
                    "padding: 2px;"
                )
                label.setFont(get_font(monospace=True, small=True))
                layout_cell.addWidget(label)

            layout_cell.addStretch(1)

    def _init_signals(self):
        pass


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    MarkHelpDialog().exec_()
    app.exec_()
