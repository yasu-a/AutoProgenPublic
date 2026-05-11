from PyQt5.QtCore import QObject

from control.widget_plain_text_edit import PlainTextEdit
from usecase.global_settings import GlobalSettingsGetUseCase


class TestCaseInputFileTextEdit(PlainTextEdit):
    def __init__(self, parent: QObject = None, *, global_settings_get_usecase: GlobalSettingsGetUseCase):
        super().__init__(parent)
        self._global_settings_get_usecase = global_settings_get_usecase

        self.__init_ui()

    def __init_ui(self):
        self.setEnabled(False)
        self.setReadOnly(False)
        settings = self._global_settings_get_usecase.execute()
        self.set_show_editing_symbols(
            settings.show_editing_symbols_in_stream_content,
        )
        self.set_line_wrap(
            settings.enable_line_wrap_in_stream_content,
        )
        self.setPlainText("")

    def set_data(self, source_code_text: str | None):
        if source_code_text is None:
            self.setEnabled(False)
            self.setPlainText("")
        else:
            self.setEnabled(True)
            self.setPlainText(source_code_text)

    def get_data(self) -> str | None:
        if self.isEnabled():
            return self.toPlainText()
        else:
            return None
