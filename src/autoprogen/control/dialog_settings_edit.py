from copy import deepcopy
from typing import Generic, TypeVar, cast

from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from autoprogen.util.app_logging import create_logger


_DataType = TypeVar("_DataType")
_UNSET = object()


class AbstractSettingsEditDialog(QDialog, Generic[_DataType]):
    """設定の明示保存と未保存変更の破棄確認を共通化する基底ダイアログ。"""

    # QDialogとABCはメタクラスが競合するため、QDialogの継承を優先する。
    # 抽象メソッド相当の契約はNotImplementedErrorで表現する。

    _logger = create_logger()

    def __init__(
            self,
            parent: QWidget | None = None,
    ) -> None:
        """編集領域と標準の保存・キャンセルボタンを構築する。"""
        super().__init__(parent)
        self._initial_data: _DataType | object = _UNSET
        self._has_changes = False

        self._layout = QVBoxLayout(self)
        self._buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel,
            parent=self,
        )
        self._buttons.button(QDialogButtonBox.Save).setText("保存")
        self._buttons.button(QDialogButtonBox.Cancel).setText("キャンセル")
        self._buttons.button(QDialogButtonBox.Save).clicked.connect(self._save)
        self._buttons.rejected.connect(self.reject)

    @property
    def content_layout(self) -> QVBoxLayout:
        """具象ダイアログが編集Widgetを配置するレイアウトを返す。"""
        return self._layout

    @property
    def has_changes(self) -> bool:
        """このダイアログで変更内容を保存した場合にTrueを返す。"""
        return self._has_changes

    def add_standard_buttons(self) -> None:
        """編集Widgetの配置後に標準ボタンをダイアログ下部へ追加する。"""
        self._layout.addWidget(self._buttons)

    def set_data(self, data: _DataType) -> None:
        """比較用の初期値を保持し、具象ダイアログへ編集値を設定する。"""
        # 編集Widgetによる参照先の変更から比較用の初期値を保護する。
        self._initial_data = deepcopy(data)
        self._set_data(data)

    def _set_data(self, data: _DataType) -> None:
        """具象ダイアログの編集Widgetへ値を設定する。"""
        raise NotImplementedError()

    def get_data(self) -> _DataType:
        """具象ダイアログの編集Widgetから現在値を取得する。"""
        raise NotImplementedError()

    def save_data(self, data: _DataType) -> None:
        """具象ダイアログに対応するUseCaseを通じて設定を保存する。"""
        raise NotImplementedError()

    def has_unsaved_changes(self) -> bool:
        """初期表示後に保存されていない変更が加えられたか返す。"""
        if self._initial_data is _UNSET:
            return False
        try:
            return self.get_data() != cast(_DataType, self._initial_data)
        except Exception:
            # 不完全な入力をモデル化できない場合も、破棄確認が必要な変更として扱う。
            return True

    def _save(self) -> None:
        """現在値に変更がある場合だけ保存し、成功後にダイアログを閉じる。"""
        try:
            data = self.get_data()
            if self._initial_data is _UNSET or data != self._initial_data:
                self.save_data(data)
                self._has_changes = True
                self._initial_data = deepcopy(data)
        except Exception as error:
            self._logger.exception("設定の保存に失敗しました")
            QMessageBox.critical(
                self,
                self.windowTitle(),
                f"設定を保存できませんでした。\n{error}",
            )
            return
        self.accept()

    def reject(self) -> None:
        """未保存の変更がある場合は、保存・破棄・編集継続を選択させる。"""
        if not self.has_unsaved_changes():
            super().reject()
            return

        choice = self._confirm_unsaved_changes()
        if choice == QMessageBox.Discard:
            super().reject()
        elif choice == QMessageBox.Save:
            # 通常の「保存」ボタンと同じ処理を使い、保存成功時のみ閉じる。
            self._save()

    def _confirm_unsaved_changes(self) -> int:
        """未保存の編集を保存・破棄するか、編集に戻るか確認する。"""
        message_box = QMessageBox(self)
        message_box.setIcon(QMessageBox.Warning)
        message_box.setWindowTitle(self.windowTitle())
        message_box.setText("保存されていない変更があります。")
        message_box.setInformativeText("変更を保存してから閉じますか？")
        message_box.setStandardButtons(
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
        )
        message_box.setDefaultButton(QMessageBox.Cancel)
        message_box.setEscapeButton(QMessageBox.Cancel)
        message_box.button(QMessageBox.Save).setText("保存して閉じる")
        message_box.button(QMessageBox.Discard).setText("破棄")
        message_box.button(QMessageBox.Cancel).setText("戻る")
        return message_box.exec_()
