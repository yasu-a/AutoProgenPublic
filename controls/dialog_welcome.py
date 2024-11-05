from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from controls.dto.new_project_config import NewProjectConfig
from controls.widget_new_project import NewProjectWidget
from controls.widget_recent_project import RecentProjectWidget
from domain.models.values import ProjectID


class WelcomeDialog(QDialog):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._result: ProjectID | NewProjectConfig | None = None

        self._init_ui()

    def _init_ui(self):
        # noinspection PyUnresolvedReferences
        self.setWindowTitle("WELCOME")
        self.setModal(True)
        self.resize(800, 500)

        layout_root = QVBoxLayout()
        self.setLayout(layout_root)

        self._container = QTabWidget(self)
        layout_root.addWidget(self._container)

        # noinspection PyTypeChecker
        self._w_new_project = NewProjectWidget(self)
        self._w_new_project.accepted.connect(self.__w_new_project_accepted)
        self._container.addTab(self._w_new_project, "")

        # noinspection PyTypeChecker
        self._w_recent_projects = RecentProjectWidget(self)
        self._w_recent_projects.accepted.connect(self.__w_recent_projects_accepted)
        self._container.addTab(self._w_recent_projects, "")

        # タブを左横にする
        self._container.setTabPosition(QTabWidget.West)  # これだけだと文字が90度傾く
        self._container.tabBar().setTabButton(
            0,
            QTabBar.LeftSide,
            QLabel("新しいプロジェクト", self),
        )
        self._container.tabBar().setTabButton(
            1,
            QTabBar.LeftSide,
            QLabel("最近のプロジェクト", self),
        )

    @pyqtSlot(NewProjectConfig)
    def __w_new_project_accepted(self, new_project_config: NewProjectConfig):
        self._result = new_project_config
        self.accept()

    @pyqtSlot(ProjectID)
    def __w_recent_projects_accepted(self, project_id: ProjectID):
        self._result = project_id
        self.accept()

    def get_data(self) -> NewProjectConfig | ProjectID | None:
        return self._result

    def showEvent(self, evt):
        if self._w_recent_projects.get_recent_project_count() == 0:
            self._container.setCurrentIndex(0)
        else:
            self._container.setCurrentIndex(1)
