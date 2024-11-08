from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QMessageBox, QInputDialog

from controls.res.icons import get_icon
from controls.widget_file_tab import AbstractFileTabWidgetDelegator, FileTabWidget
from controls.widget_plain_text_edit import PlainTextEdit
from domain.models.input_file import InputFile, InputFileMapping
from domain.models.values import FileID, SpecialFileType


class TestCaseInputFileEditWidgetDelegator(AbstractFileTabWidgetDelegator):
    def add_button_context_menu_titles(self, tab_widget: "FileTabWidget") \
            -> dict[str, tuple[str, QIcon | None]]:
        dct = dict(
            add_stdin=("標準入力", get_icon("console")),
            add_file=("ファイル", get_icon("article")),
        )
        if tab_widget.item_has_file_id(FileID.STDIN):
            dct.pop("add_stdin")
        return dct

    @classmethod
    def create_widget(cls, tab_widget, content_text: str = None) -> QWidget:
        widget = PlainTextEdit(tab_widget)
        widget.set_show_editing_symbols(False)
        if content_text is not None:
            widget.setPlainText(content_text)
        return widget

    @classmethod
    def __input_new_file_name(cls, title, tab_widget,
                              initial_file_name: str = None) -> FileID | None:
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

    def perform_add(self, action_name: str, tab_widget: "FileTabWidget") -> None:
        if action_name == "add_stdin":
            if tab_widget.item_has_file_id(FileID.STDIN):
                QMessageBox.critical(
                    tab_widget,
                    "標準入力の追加",
                    "標準入力がすでに存在します。"
                )
                return
            tab_widget.item_insert(
                index=0,
                file_id=FileID.STDIN,
                widget=self.create_widget(tab_widget),
            )
        elif action_name == "add_file":
            new_file_id = self.__input_new_file_name("ファイルの追加", tab_widget)
            if new_file_id is None:
                return
            # noinspection PyTypeChecker
            widget = PlainTextEdit(tab_widget)
            widget.set_show_editing_symbols(False)
            tab_widget.item_append(
                file_id=new_file_id,
                widget=self.create_widget(tab_widget),
            )
        else:
            assert False, action_name

    def perform_rename(self, index: int, tab_widget: "FileTabWidget") -> None:
        current_file_id = tab_widget.item_get_file_id(index)
        if current_file_id.is_special:
            QMessageBox.critical(
                tab_widget,
                "ファイル名の変更",
                "このファイルの名前は変えられません"
            )
            return

        new_file_id = self.__input_new_file_name(
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


class TestCaseInputFileEditWidget(FileTabWidget):
    def __init__(self, parent: QObject = None):
        self.__delegator = TestCaseInputFileEditWidgetDelegator()
        super().__init__(parent, delegator=self.__delegator)

    def set_data(self, input_files: InputFileMapping) -> None:
        self.item_clear()
        for file_id, input_file in input_files.items():
            self.item_append(
                file_id=file_id,
                widget=self.__delegator.create_widget(self, content_text=input_file.content_string),
            )

    @pyqtSlot()
    def get_data(self) -> InputFileMapping:
        input_files = InputFileMapping()
        for index in range(self.item_count()):  # 各タブに対して
            # タイトル
            file_id = self.item_get_file_id(index)
            # 内容
            widget = self.item_widget(index)
            assert isinstance(widget, PlainTextEdit)
            content_string = widget.toPlainText()
            # データに設定
            input_files[file_id] = InputFile(
                file_id=file_id,
                content=content_string,
            )
        return input_files
