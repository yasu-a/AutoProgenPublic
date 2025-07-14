from PyQt5.QtCore import QObject
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox, QWidget

from controls.delegator_testcase_files_edit import AbstractTestCaseFilesEditWidgetDelegator
from controls.widget_file_tab import FileTabWidget
from controls.widget_testcase_output_file_edit import ExpectedOutputFileEditWidget
from domain.models.expected_output_file import ExpectedOutputFile, ExpectedOutputFileMapping
from domain.models.values import FileID
from res.icons import get_icon


class TestCaseOutputFilesEditWidgetDelegator(AbstractTestCaseFilesEditWidgetDelegator):
    def add_button_context_menu_titles(self, tab_widget: "FileTabWidget") \
            -> dict[str, tuple[str, QIcon | None]]:
        dct = dict(
            add_stdout=("標準出力", get_icon("console")),
            add_file=("ファイル", get_icon("article")),
        )
        if tab_widget.item_has_file_id(FileID.STDOUT):
            dct.pop("add_stdout")
        return dct

    @classmethod
    def create_widget(cls, file_id, tab_widget, expected_output_file: ExpectedOutputFile = None) \
            -> QWidget:
        widget = ExpectedOutputFileEditWidget(tab_widget)
        if expected_output_file is None:
            expected_output_file = ExpectedOutputFile.create_default(file_id=file_id)
        widget.set_data(expected_output_file)
        return widget

    def perform_add(self, action_name: str, tab_widget: "FileTabWidget") -> None:
        if action_name == "add_stdout":
            if tab_widget.item_has_file_id(FileID.STDOUT):
                QMessageBox.critical(
                    tab_widget,
                    "標準出力の追加",
                    "標準出力がすでに存在します。"
                )
                return
            tab_widget.item_insert(
                index=0,
                file_id=FileID.STDOUT,
                widget=self.create_widget(FileID.STDOUT, tab_widget),
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


class TestCaseExpectedOutputFilesEditWidget(FileTabWidget):
    def __init__(self, parent: QObject = None):
        self.__delegator = TestCaseOutputFilesEditWidgetDelegator()
        super().__init__(parent, delegator=self.__delegator)

    def set_data(self, output_files: ExpectedOutputFileMapping) -> None:
        self.item_clear()
        for file_id, output_file in output_files.items():
            self.item_append(
                file_id=file_id,
                widget=self.__delegator.create_widget(file_id, self, output_file),
            )

    def get_data(self) -> ExpectedOutputFileMapping:
        output_files = ExpectedOutputFileMapping()
        for index in range(self.item_count()):  # 各タブに対して
            file_id = self.item_get_file_id(index)
            # 内容
            widget = self.item_widget(index)
            assert isinstance(widget, ExpectedOutputFileEditWidget)
            # データに設定
            output_files[file_id] = widget.get_data(file_id)
        return output_files
