from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout, qApp

from res.fonts import get_font


class AboutDialog(QDialog):
    # 採点画面

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        self.setWindowTitle("About")
        self.setModal(True)

        layout = QHBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        self.setLayout(layout)

        if "left":
            layout_left = QVBoxLayout()
            layout_left.setAlignment(Qt.AlignVCenter)
            layout.addLayout(layout_left)

            self._l_app_icon = QLabel(self)
            self._l_app_icon.setPixmap(qApp.windowIcon().pixmap(42, 42))
            layout_left.addWidget(self._l_app_icon)

            layout_left.addStretch(1)

        if "right":
            layout_right = QVBoxLayout()
            layout_right.setSpacing(5)
            layout.addLayout(layout_right)

            self._l_title = QLabel(self)
            self._l_title.setFont(get_font(bold=True))
            self._l_title.setText(f"{qApp.applicationName()} {qApp.applicationVersion()}")
            layout_right.addWidget(self._l_title)

            self._l_url = QLabel(self)
            self._l_url.setOpenExternalLinks(True)
            url = r"https://github.com/yasu-a/AutoProgenPublic"
            self._l_url.setText(f"<html><a href=\"{url}\">{url}</a></html>")
            layout_right.addWidget(self._l_url)

            layout_right.addWidget(
                QLabel("<html>Powered by PyQt5</html>", self)
            )

            url = r"https://icooon-mono.com"
            layout_right.addWidget(
                QLabel(f"<html>Icons: <a href=\"{url}\">{url}</a></html>", self)
            )

            layout_right.addStretch(1)

        self.setFixedSize(self.sizeHint())

    def _init_signals(self):
        pass
