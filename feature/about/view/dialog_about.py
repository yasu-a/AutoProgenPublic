from PyQt5.QtCore import QObject, Qt
from PyQt5.QtGui import QShowEvent
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout, qApp

from feature.about.handler.interface import IAboutDialogHandler, IAboutDialogView
from feature.about.usecase.dto import AboutInfo
from shared.view.style.font import get_font


class AboutDialog(QDialog, IAboutDialogView):
    """
    Aboutダイアログ
    Handlerパターンを使用してロジックを分離
    """

    def __init__(
            self,
            parent: QObject = None,
            *,
            handler: IAboutDialogHandler,
    ):
        super().__init__(parent)
        self._handler = handler

        self._init_ui()

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
            layout_right.addWidget(self._l_title)

            self._l_url = QLabel(self)
            self._l_url.setOpenExternalLinks(True)
            layout_right.addWidget(self._l_url)

            layout_right.addWidget(
                QLabel("<html>Powered by PyQt5</html>", self)
            )

            self._l_icon_credit = QLabel(self)
            self._l_icon_credit.setOpenExternalLinks(True)
            layout_right.addWidget(self._l_icon_credit)

            layout_right.addStretch(1)

        # 内容に収まる最小サイズに調整
        self.adjustSize()

    def showEvent(self, evt: QShowEvent) -> None:
        """ダイアログ表示時にHandlerに通知"""
        super().showEvent(evt)
        self._handler.on_view_initialized()

    # ===== IAboutDialogView実装 =====
    def set_about_info(self, about_info: AboutInfo) -> None:
        """About情報を設定"""
        self._l_title.setText(f"{about_info.app_name} {about_info.version_text}")
        self._l_url.setText(
            f"<html><a href=\"{about_info.repo_url}\">{about_info.repo_url}</a></html>")
        self._l_icon_credit.setText(
            f"<html>Icons: <a href=\"{about_info.icon_credit_url}\">{about_info.icon_credit_url}</a></html>")
