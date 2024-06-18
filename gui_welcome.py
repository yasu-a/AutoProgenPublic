import os

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from gui_filepath import FilePathWidget
from settings import settings_recent_projects


def is_path_to_valid_project(path: str):
    return os.path.exists(os.path.join(path, "reportlist.xlsx"))


class WelcomeWidget(QWidget):
    project_picked = pyqtSignal(str)  # type: ignore

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self.__init_ui()

    def __init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        self._w_folder_selector = FilePathWidget("フォルダを開く", False, self)
        self._w_folder_selector.selection_changed.connect(self.project_open_by_selector)
        layout.addWidget(self._w_folder_selector)

        self._l_recent = QLabel("最近のプロジェクト", self)
        layout.addWidget(self._l_recent)

        self._lw_recent_project_list = QListWidget(self)
        for recent_project in settings_recent_projects.list_sorted():
            self._lw_recent_project_list.addItem(
                str(recent_project.updated)[:-7] + " " + recent_project.fullpath
            )
        self._lw_recent_project_list.doubleClicked.connect(  # type: ignore
            self.project_open_by_recent_list
        )
        layout.addWidget(self._lw_recent_project_list)

    @pyqtSlot(str)
    def project_open_by_selector(self, path):
        if is_path_to_valid_project(path):
            self.project_picked.emit(path)
        else:
            # noinspection PyTypeChecker,PyUnresolvedReferences
            QMessageBox.warning(
                self,
                self.windowTitle(),
                "選択したフォルダはプロジェクトフォルダではありません。reportlist.xlsxを含むフォルダを選択してください。",
                QMessageBox.Ok
            )

    @pyqtSlot()
    def project_open_by_recent_list(self):
        index = self._lw_recent_project_list.currentRow()
        path = settings_recent_projects.list_sorted()[index].fullpath
        if is_path_to_valid_project(path):
            self.project_picked.emit(path)
        else:
            # noinspection PyTypeChecker,PyUnresolvedReferences
            QMessageBox.warning(
                self,
                self.windowTitle(),
                "選択したフォルダはプロジェクトフォルダではありません。reportlist.xlsxを含むフォルダを選択してください。",
                QMessageBox.Ok
            )


class WelcomeDialog(QDialog):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self.__path = None

        self.__init_ui()

    def __init_ui(self):
        self.setModal(True)
        # noinspection PyUnresolvedReferences
        self.setWindowTitle("Welcome")
        self.resize(700, 200)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self._w_welcome = WelcomeWidget(self)  # type: ignore
        self._w_welcome.project_picked.connect(self.project_picked)
        layout.addWidget(self._w_welcome)

    @pyqtSlot(str)
    def project_picked(self, path):
        self.accept()
        settings_recent_projects.add_if_absent(path)
        settings_recent_projects.commit()
        self.__path = path

    @property
    def project_path(self) -> str:
        return self.__path
