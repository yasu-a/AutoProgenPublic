from abc import ABC, abstractmethod

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QMessageBox, QInputDialog, QWidget
)

from controls.res.icons import get_icon
from controls.widget_file_tab import AbstractFileTabWidgetDelegator, FileTabWidget
from domain.models.expected_ouput_file import ExpectedOutputFile
from domain.models.values import FileID, SpecialFileType


class AbstractTestCaseFilesEditWidgetDelegator(AbstractFileTabWidgetDelegator, ABC):
    @abstractmethod
    def add_button_context_menu_titles(self, tab_widget: "FileTabWidget") \
            -> dict[str, tuple[str, QIcon | None]]:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def create_widget(cls, file_id, tab_widget, expected_output_file: ExpectedOutputFile = None) \
            -> QWidget:
        raise NotImplementedError()

    @classmethod
    def _input_new_file_name(cls, title, tab_widget, initial_file_name: str = None) \
            -> FileID | None:
        new_file_name = initial_file_name or ""
        while True:
            # 入力を要求する
            new_file_name, ok = QInputDialog.getText(
                tab_widget,
                title,
                "新しい入力ファイル名を入力してください",
                text=new_file_name,
            )
            # キャンセルされたら中断
            if not ok:
                return None
            # 空白を取り除く
            new_file_name = new_file_name.strip()
            # 空文字なら中断
            if not new_file_name:
                return None
            # FileIDに変換できるか確認
            try:
                new_file_id = FileID(new_file_name)
            except ValueError:
                QMessageBox.critical(
                    tab_widget,
                    title,
                    f"不正なファイル名です: {new_file_name}"
                )
                continue
            # FileIDが特殊ファイルでないか確認
            if new_file_id.is_special:
                QMessageBox.critical(
                    tab_widget,
                    title,
                    f"使用できないファイル名です: {new_file_name}"
                )
                continue
            # すでに同じファイルが存在しないか確認
            if tab_widget.item_has_file_id(new_file_id):
                QMessageBox.critical(
                    tab_widget,
                    title,
                    f"同じ名前の入力ファイルが存在します。"
                )
                continue
            # 作成可能
            break
        return FileID(new_file_name)

    @abstractmethod
    def perform_add(self, action_name: str, tab_widget: "FileTabWidget") -> None:
        raise NotImplementedError()

    def perform_rename(self, index: int, tab_widget: "FileTabWidget") -> None:
        current_file_id = tab_widget.item_get_file_id(index)
        if current_file_id.is_special:
            QMessageBox.critical(
                tab_widget,
                "ファイル名の変更",
                "このファイルの名前は変えられません"
            )
            return

        new_file_id = self._input_new_file_name(
            "ファイル名の変更",
            tab_widget,
            initial_file_name=self.file_id_to_tab_title(current_file_id),
        )
        if new_file_id is None:
            return
        tab_widget.item_set_file_id(
            index=index,
            file_id=new_file_id,
        )

    def perform_delete(self, index: int, tab_widget: "FileTabWidget") -> None:
        file_id = tab_widget.item_get_file_id(index)
        title = self.file_id_to_tab_title(file_id)
        res = QMessageBox.critical(
            tab_widget,
            "ファイルの削除",
            f"ファイル {title} を削除しますか？",
            buttons=QMessageBox.Yes | QMessageBox.No,
            defaultButton=QMessageBox.No,
        )
        if res != QMessageBox.Yes:
            return
        tab_widget.item_delete(
            index=index,
        )

    def file_id_to_tab_title(self, file_id: FileID) -> str:
        if file_id.is_special:
            if file_id.special_file_type == SpecialFileType.STDIN:
                return "標準入力"
            elif file_id.special_file_type == SpecialFileType.STDOUT:
                return "標準出力"
            else:
                assert False, file_id.special_file_type
        else:
            return str(file_id.deployment_relative_path)

    def file_id_to_tab_icon(self, file_id: FileID) -> QIcon | None:
        if file_id.is_special:
            return get_icon("console")
        else:
            return get_icon("article")
