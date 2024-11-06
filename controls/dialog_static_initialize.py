from pathlib import Path

from PyQt5.QtCore import QObject

from application.dependency.usecases import get_project_initialize_static_usecase
from controls.dialog_progress import AbstractProgressDialogWorker, AbstractProgressDialog


class _StaticInitializeWorker(AbstractProgressDialogWorker):
    def __init__(self, parent: QObject = None, *, manaba_report_archive_fullpath: Path):
        super().__init__(parent)

        self._project_static_initialize_usecase = get_project_initialize_static_usecase(
            manaba_report_archive_fullpath=manaba_report_archive_fullpath,
        )

    def run(self):
        self._project_static_initialize_usecase.execute(self._callback)


class StaticInitializeProgressDialog(AbstractProgressDialog):
    # プロジェクトの静的データを初期化しプログレスを表示するダイアログ

    def __init__(self, parent: QObject = None, *, manaba_report_archive_fullpath: Path):
        super().__init__(
            parent,
            title="プロジェクトの初期化",
            worker_producer=lambda: _StaticInitializeWorker(
                self,
                manaba_report_archive_fullpath=manaba_report_archive_fullpath,
            ),
        )
