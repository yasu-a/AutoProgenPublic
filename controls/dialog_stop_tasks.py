from PyQt5.QtCore import QObject

from application.dependency.tasks import get_task_manager
from controls.dialog_progress import AbstractProgressDialogWorker, AbstractProgressDialog


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
