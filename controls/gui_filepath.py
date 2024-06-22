import os

from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog

from icons import icon


class FilePathWidget(QWidget):
    selection_changed = pyqtSignal(str)

    def __init__(self, text: str, select_file: bool, parent: QObject = None):
        super().__init__(parent)

        self._select_file = select_file

        self._init_ui(text)

    def _init_ui(self, text: str):
        layout = QHBoxLayout()
        self.setLayout(layout)

        self._l_text = QLabel(text, self)
        layout.addWidget(self._l_text)

        self._le_path = QLineEdit()
        self._le_path.setMinimumWidth(400)
        self._le_path.setReadOnly(True)
        layout.addWidget(self._le_path)

        self._b_pick_folder = QPushButton(self)
        self._b_pick_folder.setIcon(icon("open"))
        self._b_pick_folder.clicked.connect(self.prompt_pick_folder)  # type: ignore
        layout.addWidget(self._b_pick_folder)

    @pyqtSlot()
    def prompt_pick_folder(self):
        if self._select_file:
            path, _ = QFileDialog.getOpenFileUrl(self, "ファイルを選択")
            path = path.toLocalFile()
        else:
            path = str(QFileDialog.getExistingDirectory(self, "フォルダを選択"))
        if os.path.exists(path):
            self._le_path.setText(path)
            self.selection_changed.emit(path)  # type: ignore
