from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import QPushButton, QStyleOptionButton, QStyle

from res.font import get_font


class PageButton(QPushButton):
    def __init__(self, parent: QObject = None, *, text: str):
        super().__init__(parent)

        self._text = text

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        self.setText(self._text)
        self.setFont(get_font(monospace=True, large=True))

        # フォントに応じたボタンの最小サイズを求める
        # https://stackoverflow.com/questions/6639012/minimum-size-width-of-a-qpushbutton-that-is-created-from-code
        style_option = QStyleOptionButton()
        style_option.initFrom(self)
        text_size = self.fontMetrics().size(Qt.TextShowMnemonic, self.text())
        style_option.rect.setSize(text_size)
        self.setFixedSize(
            self.style().sizeFromContents(QStyle.CT_PushButton, style_option, text_size, self),
        )

        self.setFocusPolicy(Qt.NoFocus)

    def _init_signals(self):
        pass
