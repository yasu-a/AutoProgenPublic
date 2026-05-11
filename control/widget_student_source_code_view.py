from PyQt5.QtCore import QObject

from application.container import AppContainer
from control.widget_source_code_text_edit import SourceCodeTextEdit


class StudentSourceCodeView(SourceCodeTextEdit):
    def __init__(self, parent: QObject = None, *, app_container: AppContainer):
        super().__init__(parent)
        self._app_container = app_container

        self.__init_ui()

    def __init_ui(self):
        self.setEnabled(False)
        self.setReadOnly(True)
        settings = self._app_container.global_settings_get_usecase.execute()
        self.set_show_editing_symbols(
            settings.show_editing_symbols_in_source_code,
        )
        self.set_line_wrap(
            settings.enable_line_wrap_in_source_code,
        )
        self.setPlainText("")

    def set_data(self, source_code_text: str | None):
        if source_code_text is None:
            self.setEnabled(False)
            self.setPlainText("")
        else:
            self.setEnabled(True)
            self.setPlainText(source_code_text)
