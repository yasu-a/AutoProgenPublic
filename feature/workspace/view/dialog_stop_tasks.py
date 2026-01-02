from PyQt5.QtCore import QObject

from app.di.system import get_task_manager
from shared.view.dialog_progress import AbstractProgressDialog, AbstractProgressDialogWorker


class _StopTasksWorker(AbstractProgressDialogWorker):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._task_manager = get_task_manager()

    def run(self):
        self._task_manager.terminate(self._callback)


class StopTasksDialog(AbstractProgressDialog):
    # プロジェクトの静的データを初期化しプログレスを表示するダイアログ

    def __init__(self, parent: QObject = None):
        super().__init__(
            parent,
            title="タスクの停止",
            worker_producer=lambda: _StopTasksWorker(
                self,
            ),
        )
