from PyQt5.QtCore import QObject

from controls.widget_source_text_edit import SourceTextEdit


class StudentSourceCodeViewWidget(SourceTextEdit):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self.__init_ui()

    def __init_ui(self):
        self.setEnabled(False)
        self.setReadOnly(True)
        self.setPlainText("")

    def set_data(self, source_code_text: str | None):
        if source_code_text is None:
            self.setEnabled(False)
            self.setPlainText("")
        else:
            self.setEnabled(True)
            self.setPlainText(source_code_text)
