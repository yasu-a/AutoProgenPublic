from PyQt5.QtCore import *
from PyQt5.QtGui import QShowEvent
from PyQt5.QtWidgets import *

from application.dependency.usecases import get_project_list_recent_summary_usecase
from controls.dto.new_project_config import NewProjectConfig
from controls.res.icons import get_icon
from controls.widget_new_project import NewProjectWidget
from controls.widget_recent_project import RecentProjectWidget
from domain.models.values import ProjectID


class WelcomeDialog(QDialog):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._result: ProjectID | NewProjectConfig | None = None

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        # noinspection PyUnresolvedReferences
        self.setWindowTitle("WELCOME")
        self.setModal(True)
        self.resize(800, 400)

        layout_root = QVBoxLayout()
        self.setLayout(layout_root)

        self._container = QTabWidget(self)
        layout_root.addWidget(self._container)

        # noinspection PyTypeChecker
        self._w_new_project = NewProjectWidget(self)
        self._container.addTab(self._w_new_project, "")

        # noinspection PyTypeChecker
        self._w_recent_projects = RecentProjectWidget(self)
        self._container.addTab(self._w_recent_projects, "")

        # タブを左横にする
        self._container.setTabPosition(QTabWidget.West)  # これだけだと文字が90度傾く
        self._container.tabBar().setTabIcon(0, get_icon("plus", rotate=90))
        self._container.tabBar().setTabButton(
            0,
            QTabBar.LeftSide,
            QLabel("新しいプロジェクト", self),
        )
        self._container.tabBar().setTabIcon(1, get_icon("article", rotate=90))
        self._container.tabBar().setTabButton(
            1,
            QTabBar.LeftSide,
            QLabel("最近のプロジェクト", self),
        )

    def _init_signals(self):
        self._w_new_project.accepted.connect(self.__w_new_project_accepted)
        self._w_recent_projects.accepted.connect(self.__w_recent_projects_accepted)
        # noinspection PyUnresolvedReferences
        self.finished.connect(self.__finished)

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

    # noinspection PyMethodOverriding
    def showEvent(self, evt: QShowEvent):
        # TODO: ProjectCountUseCaseを実装して置き換える　プロジェクトデータを全て読み込む必要はないため
        if get_project_list_recent_summary_usecase().execute():
            self._container.setCurrentIndex(1)
        else:
            self._container.setCurrentIndex(0)
        self._w_recent_projects.start_worker()

    # noinspection PyMethodOverriding
    @pyqtSlot()
    def __finished(self):
        self._w_recent_projects.stop_worker()
