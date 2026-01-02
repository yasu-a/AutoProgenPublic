from PyQt5.QtCore import QObject, Qt
from PyQt5.QtGui import QCloseEvent, QShowEvent
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton

from feature.setting.handler.interface import ISettingEditHandler
from feature.setting.view.widget_settings_edit import SettingEditWidget


class SettingEditDialog(QDialog):
    """
    設定ダイアログ
    Handlerパターンを使用してロジックを分離
    """

    def __init__(
            self,
            parent: QObject = None,
            *,
            handler: ISettingEditHandler,
    ):
        super().__init__(parent)
        self._handler = handler

        self._init_ui()

    def _init_ui(self):
        # noinspection PyUnresolvedReferences
        self.setWindowTitle("設定")
        self.setModal(True)
        self.resize(700, 700)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Viewを生成
        self._w_settings_edit = SettingEditWidget(self)  # type: ignore

        # HandlerをViewに設定
        self._w_settings_edit.set_handler(self._handler)

        layout.addWidget(self._w_settings_edit)

        # ボタンエリア
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        
        self._b_cancel = QPushButton("キャンセル", self)
        self._b_save = QPushButton("保存", self)
        
        button_layout.addWidget(self._b_cancel)
        button_layout.addWidget(self._b_save)
        
        layout.addLayout(button_layout)

        # シグナル接続
        self._b_cancel.clicked.connect(self.__b_cancel_clicked)  # type: ignore
        self._b_save.clicked.connect(self.__b_save_clicked)  # type: ignore

    @property
    def settings_edit_widget(self) -> SettingEditWidget:
        """設定編集ウィジェットを取得（Navigatorからアクセス用）"""
        return self._w_settings_edit

    def showEvent(self, evt: QShowEvent) -> None:
        """ダイアログ表示時にHandlerに通知"""
        super().showEvent(evt)
        self._handler.on_view_initialized()

    def __b_cancel_clicked(self):
        """キャンセルボタンがクリックされたとき"""
        can_close = self._handler.on_cancel_requested()
        if can_close:
            self.accept()

    def __b_save_clicked(self):
        """保存ボタンがクリックされたとき"""
        can_close = self._handler.on_save_button_clicked()
        if can_close:
            self.accept()

    # noinspection PyMethodOverriding
    def closeEvent(self, evt: QCloseEvent):
        """ダイアログが閉じられるとき（×ボタン） → Handlerに委譲"""
        can_close = self._handler.on_close_requested()
        if not can_close:
            evt.ignore()
            return

        evt.accept()
