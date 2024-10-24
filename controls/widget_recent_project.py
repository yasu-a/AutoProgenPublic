from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from application.dependency.usecases import get_recent_project_list_usecase
from domain.models.values import ProjectID
from usecases.dto.project_summary import ProjectSummary


class RecentProjectListColumns:
    COL_NAME = 0
    COL_TARGET_ID = 1
    COL_MTIME = 2
    HEADER = "プロジェクト名", "設問番号", "最後に開いた日時"


class RecentProjectModel(QAbstractTableModel):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._project_summary_lst: list[ProjectSummary] \
            = get_recent_project_list_usecase().execute()

    def data(self, index: QModelIndex, role=None):
        if role == Qt.DisplayRole:
            if index.column() == RecentProjectListColumns.COL_NAME:
                return self._project_summary_lst[index.row()].project_name
            elif index.column() == RecentProjectListColumns.COL_TARGET_ID:
                return self._project_summary_lst[index.row()].target_number
            elif index.column() == RecentProjectListColumns.COL_MTIME:
                return str(self._project_summary_lst[index.row()].open_at)[:-7]

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self._project_summary_lst)

    def columnCount(self, *args, **kwargs):
        return len(RecentProjectListColumns.HEADER)

    def headerData(self, section: int, orientation, role=None):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return RecentProjectListColumns.HEADER[section]
            elif orientation == Qt.Vertical:
                return ""

    def get_project_id(self, row: int) -> ProjectID:
        return self._project_summary_lst[row].project_id


class RecentProjectWidget(QGroupBox):
    # noinspection PyArgumentList
    accepted = pyqtSignal(ProjectID)

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._model_recent_projects = RecentProjectModel()
        self._init_ui()

    def _init_ui(self):
        self.setTitle("最近のプロジェクト")

        layout = QVBoxLayout()
        self.setLayout(layout)

        self._table_recent_projects = QTableView(self)
        self._table_recent_projects.setModel(self._model_recent_projects)
        # noinspection PyTypeChecker
        self._table_recent_projects.setVerticalHeader(None)
        self._table_recent_projects.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table_recent_projects.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table_recent_projects.setColumnWidth(RecentProjectListColumns.COL_NAME, 150)
        self._table_recent_projects.setColumnWidth(RecentProjectListColumns.COL_TARGET_ID, 100)
        self._table_recent_projects.horizontalHeader().setStretchLastSection(True)
        # noinspection PyUnresolvedReferences
        self._table_recent_projects.doubleClicked.connect(
            self._table_recent_projects_double_clicked
        )
        layout.addWidget(self._table_recent_projects)

    def _table_recent_projects_double_clicked(self, index: QModelIndex):
        self.accepted.emit(self._model_recent_projects.get_project_id(index.row()))
