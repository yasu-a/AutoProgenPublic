from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from application.dependency.services import get_project_list_service
from domain.models.values import ProjectName


class RecentProjectListColumns:
    COL_NAME = 0
    COL_TARGET_ID = 1
    COL_MTIME = 2
    HEADER = "プロジェクト名", "設問番号", "最後に開いた日時"


class RecentProjectModel(QAbstractTableModel):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._stats = get_project_list_service().list_project_stats()

    def data(self, index: QModelIndex, role=None):
        if role == Qt.DisplayRole:
            if index.column() == RecentProjectListColumns.COL_NAME:
                return str(self._stats[index.row()].project_name)
            elif index.column() == RecentProjectListColumns.COL_TARGET_ID:
                return int(self._stats[index.row()].target_id)
            elif index.column() == RecentProjectListColumns.COL_MTIME:
                return str(self._stats[index.row()].mtime)

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self._stats)

    def columnCount(self, *args, **kwargs):
        return len(RecentProjectListColumns.HEADER)

    def headerData(self, section: int, orientation, role=None):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return RecentProjectListColumns.HEADER[section]
            elif orientation == Qt.Vertical:
                return ""

    def get_project_name(self, row: int) -> ProjectName:
        return self._stats[row].project_name


class RecentProjectWidget(QGroupBox):
    # noinspection PyArgumentList
    accepted = pyqtSignal(ProjectName)

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
        self.accepted.emit(self._model_recent_projects.get_project_name(index.row()))
