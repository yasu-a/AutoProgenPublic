from PyQt5.QtCore import QObject

from application.dependency.usecase import get_global_settings_get_usecase
from control.widget_source_code_text_edit import SourceCodeTextEdit


class StudentSourceCodeView(SourceCodeTextEdit):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self.__init_ui()

    def __init_ui(self):
        self.setEnabled(False)
        self.setReadOnly(True)
        self.set_show_editing_symbols(
            get_global_settings_get_usecase().execute().show_editing_symbols_in_source_code,
        )
        self.set_line_wrap(
            get_global_settings_get_usecase().execute().enable_line_wrap_in_source_code,
        )
        self.setPlainText("")

    def set_data(self, source_code_text: str | None):
        if source_code_text is None:
            self.setEnabled(False)
            self.setPlainText("")
        else:
            self.setEnabled(True)
            self.setPlainText(source_code_text)
