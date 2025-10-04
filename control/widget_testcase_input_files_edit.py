from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox, QWidget

from control.delegator_testcase_files_edit import AbstractTestCaseFilesEditWidgetDelegator
from control.widget_file_tab import FileTabWidget
from control.widget_testcase_input_file_text_edit import TestCaseInputFileTextEdit
from domain.model.input_file import InputFileCollection, InputFile
from domain.model.value import FileID
from res.icon import get_icon


class TestCaseInputFilesEditWidgetDelegator(AbstractTestCaseFilesEditWidgetDelegator):
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
    def create_widget(cls, file_id, tab_widget, content_text: str = None) -> QWidget:
        _ = file_id
        widget = TestCaseInputFileTextEdit(tab_widget)
        if content_text is None:
            content_text = ""
        widget.set_data(content_text)
        return widget

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
                widget=self.create_widget(FileID.STDIN, tab_widget),
            )
        elif action_name == "add_file":
            new_file_id = self._input_new_file_name("ファイルの追加", tab_widget)
            if new_file_id is None:
                return
            # noinspection PyTypeChecker
            tab_widget.item_append(
                file_id=new_file_id,
                widget=self.create_widget(new_file_id, tab_widget),
            )
        else:
            assert False, action_name


class TestCaseInputFilesEditWidget(FileTabWidget):
    def __init__(self, parent: QObject = None):
        self.__delegator = TestCaseInputFilesEditWidgetDelegator()
        super().__init__(parent, delegator=self.__delegator)

    def set_data(self, input_file_collection: InputFileCollection) -> None:
        self.item_clear()
        for file_id, input_file in input_file_collection.items():
            self.item_append(
                file_id=file_id,
                widget=self.__delegator.create_widget(
                    file_id,
                    self,
                    content_text=input_file.content_string,
                ),
            )

    @pyqtSlot()
    def get_data(self) -> InputFileCollection:
        input_file_collection = InputFileCollection()
        for index in range(self.item_count()):  # 各タブに対して
            file_id = self.item_get_file_id(index)
            # 内容
            widget = self.item_widget(index)
            assert isinstance(widget, TestCaseInputFileTextEdit)
            # データに設定
            input_file_collection.put(
                InputFile(
                    file_id=file_id,
                    content=widget.get_data(),
                )
            )
        return input_file_collection
