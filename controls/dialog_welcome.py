from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from controls.widget_new_project import NewProjectWidget
from controls.widget_recent_project import RecentProjectWidget
from models.new_project_config import NewProjectConfig
from models.values import ProjectName


class WelcomeDialog(QDialog):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._result: ProjectName | NewProjectConfig | None = None

        self._init_ui()

    def _init_ui(self):
        # noinspection PyUnresolvedReferences
        self.setWindowTitle("Welcome")
        self.setModal(True)
        self.resize(500, 500)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # noinspection PyTypeChecker
        self._w_new_project = NewProjectWidget(self)
        self._w_new_project.accepted.connect(self._w_new_project_accepted)
        layout.addWidget(self._w_new_project)

        # noinspection PyTypeChecker
        self._w_recent_projects = RecentProjectWidget(self)
        self._w_recent_projects.accepted.connect(self._w_recent_projects_accepted)
        layout.addWidget(self._w_recent_projects)

    @pyqtSlot(NewProjectConfig)
    def _w_new_project_accepted(self, new_project_config: NewProjectConfig):
        self._result = new_project_config
        self.accept()

    @pyqtSlot(ProjectName)
    def _w_recent_projects_accepted(self, project_name: ProjectName):
        self._result = project_name
        self.accept()

    def get_result(self) -> NewProjectConfig | ProjectName | None:
        return self._result
