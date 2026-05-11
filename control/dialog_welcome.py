from PyQt5.QtCore import *
from PyQt5.QtGui import QShowEvent
from PyQt5.QtWidgets import *

from control.dto.new_project_config import NewProjectConfig
from control.widget_new_project import NewProjectWidget
from control.widget_recent_project import RecentProjectWidget
from domain.model.value import ProjectID
from res.icon import get_icon
from usecase.manaba_report_archive import ManabaReportArchiveValidateMasterExcelExistsUseCase
from usecase.project import (
    ProjectBaseFolderShowUseCase,
    ProjectCheckExistByNameUseCase,
    ProjectDeleteUseCase,
    ProjectFolderShowUseCase,
    ProjectGetSizeQueryUseCase,
    ProjectListRecentSummaryUseCase,
)


class WelcomeDialog(QDialog):
    def __init__(
            self,
            parent: QObject = None,
            *,
            project_check_exist_by_name_usecase: ProjectCheckExistByNameUseCase,
            manaba_report_archive_validate_master_excel_exists_usecase: ManabaReportArchiveValidateMasterExcelExistsUseCase,
            project_list_recent_summary_usecase: ProjectListRecentSummaryUseCase,
            project_folder_show_usecase: ProjectFolderShowUseCase,
            project_delete_usecase: ProjectDeleteUseCase,
            project_base_folder_show_usecase: ProjectBaseFolderShowUseCase,
            project_get_size_query_usecase: ProjectGetSizeQueryUseCase,
    ):
        super().__init__(parent)

        self._project_check_exist_by_name_usecase = project_check_exist_by_name_usecase
        self._manaba_report_archive_validate_master_excel_exists_usecase = (
            manaba_report_archive_validate_master_excel_exists_usecase
        )
        self._project_list_recent_summary_usecase = project_list_recent_summary_usecase
        self._project_folder_show_usecase = project_folder_show_usecase
        self._project_delete_usecase = project_delete_usecase
        self._project_base_folder_show_usecase = project_base_folder_show_usecase
        self._project_get_size_query_usecase = project_get_size_query_usecase
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
        self._w_new_project = NewProjectWidget(
            self,
            project_check_exist_by_name_usecase=self._project_check_exist_by_name_usecase,
            manaba_report_archive_validate_master_excel_exists_usecase=(
                self._manaba_report_archive_validate_master_excel_exists_usecase
            ),
        )
        self._container.addTab(self._w_new_project, "")

        # noinspection PyTypeChecker
        self._w_recent_projects = RecentProjectWidget(
            self,
            project_list_recent_summary_usecase=self._project_list_recent_summary_usecase,
            project_folder_show_usecase=self._project_folder_show_usecase,
            project_delete_usecase=self._project_delete_usecase,
            project_base_folder_show_usecase=self._project_base_folder_show_usecase,
            project_get_size_query_usecase=self._project_get_size_query_usecase,
        )
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
        if self._project_list_recent_summary_usecase.execute():
            self._container.setCurrentIndex(1)
        else:
            self._container.setCurrentIndex(0)
        self._w_recent_projects.start_worker()

    # noinspection PyMethodOverriding
    @pyqtSlot()
    def __finished(self):
        self._w_recent_projects.stop_worker()
