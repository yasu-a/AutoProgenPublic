from pathlib import Path

from PyQt5.QtCore import QObject
from PyQt5.QtGui import QCloseEvent

from app.di.usecase import get_current_project_initialize_static_usecase
from feature.projman.usecase.dto import ProjectInitializeResult
from shared.view.dialog_progress import AbstractProgressDialog, AbstractProgressDialogWorker


class _ProjectInitializeWorker(AbstractProgressDialogWorker[ProjectInitializeResult]):
    def __init__(self, parent: QObject = None, *, manaba_report_archive_fullpath: Path):
        super().__init__(parent)

        self._current_project_static_initialize_usecase = get_current_project_initialize_static_usecase(
            manaba_report_archive_fullpath=manaba_report_archive_fullpath,
        )

    def run(self):
        result: ProjectInitializeResult \
            = self._current_project_static_initialize_usecase.execute(self._callback)
        if result.has_error:
            self.set_rejected(result)


class ProjectInitializeProgressDialog(AbstractProgressDialog[ProjectInitializeResult]):
    # プロジェクトの静的データを初期化しプログレスを表示するダイアログ

    def __init__(self, parent: QObject = None, *, manaba_report_archive_fullpath: Path):
        super().__init__(
            parent,
            title="プロジェクトの初期化",
            worker_producer=lambda: _ProjectInitializeWorker(
                self,
                manaba_report_archive_fullpath=manaba_report_archive_fullpath,
            ),
        )

    def closeEvent(self, evt: QCloseEvent):
        super().closeEvent(evt)
