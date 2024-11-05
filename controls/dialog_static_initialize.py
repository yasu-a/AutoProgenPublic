from pathlib import Path

from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot, Qt
from PyQt5.QtGui import QShowEvent
from PyQt5.QtWidgets import QDialog, QLabel, QHBoxLayout

from application.dependency.usecases import get_project_initialize_static_usecase
from controls.widget_progress_icon import ProgressIconWidget
from utils.app_logging import create_logger


class _StaticInitializeWorker(QThread):
    progress_updated = pyqtSignal(str, name="progress_updated")  # progress-title: str
    progress_finished = pyqtSignal(name="progress_finished")

    def __init__(self, parent: QObject = None, *, manaba_report_archive_fullpath: Path):
        super().__init__(parent)

        self._project_static_initialize_usecase = get_project_initialize_static_usecase(
            manaba_report_archive_fullpath=manaba_report_archive_fullpath,
        )

    def __usecase_callback(self, progres_title: str) -> None:
        # noinspection PyUnresolvedReferences
        self.progress_updated.emit(progres_title)

    def run(self):
        self._project_static_initialize_usecase.execute(self.__usecase_callback)
        # noinspection PyUnresolvedReferences
        self.progress_finished.emit()


class StaticInitializeProgressDialog(QDialog):
    # プロジェクトの静的データを初期化しプログレスを表示するダイアログ

    _logger = create_logger()

    def __init__(self, parent: QObject = None, *, manaba_report_archive_fullpath: Path):
        super().__init__(parent)

        self._worker = _StaticInitializeWorker(
            self,
            manaba_report_archive_fullpath=manaba_report_archive_fullpath,
        )

        self._init_ui()
        self._init_signals()

    def _init_ui(self):
        self.setWindowTitle("プロジェクトの初期化")
        self.setModal(True)
        self.resize(700, 40)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        layout = QHBoxLayout()
        self.setLayout(layout)

        self._w_progress_icon = ProgressIconWidget(self)
        layout.addWidget(self._w_progress_icon)

        self._w_progress_title = QLabel(self)
        layout.addWidget(self._w_progress_title)

    def _init_signals(self):
        # noinspection PyUnresolvedReferences
        self._worker.progress_updated.connect(self.__worker_progress_updated)
        # noinspection PyUnresolvedReferences
        self._worker.progress_finished.connect(self.__worker_progress_finished)

    def showEvent(self, evt: QShowEvent):
        self._worker.start()

    @pyqtSlot(str)
    def __worker_progress_updated(self, progress_title: str):
        self._w_progress_title.setText(progress_title)

    @pyqtSlot()
    def __worker_progress_finished(self):
        self.accept()
