from typing import TypeVar, Callable
from PyQt5.QtCore import QThread, pyqtSignal, QObject

T = TypeVar('T')


class BlockingTaskWorker(QThread):
    """
    ブロッキングタスクを実行するWorkerスレッド
    
    task_funcは必ずprogress_callbackをキーワード引数として受け取ること
    """
    progress_updated = pyqtSignal(str, name="progress_updated")
    finished = pyqtSignal(name="finished")

    def __init__(self, parent: QObject = None, task_func: Callable[..., T] = None, **kwargs):
        """
        Args:
            parent: 親オブジェクト
            task_func: 実行する関数（progress_callbackをキーワード引数として必須で受け取ること）
            **kwargs: task_funcに渡す追加のキーワード引数
        """
        super().__init__(parent)
        self._task_func = task_func
        self._task_kwargs = kwargs
        self._result: T | None = None
        self._error: Exception | None = None

    def run(self):
        """タスクを実行する"""
        try:
            kwargs = dict(self._task_kwargs)
            # progress_callbackを必ず渡す
            self._result = self._task_func(progress_callback=self._progress_callback, **kwargs)
        except Exception as e:
            self._error = e
        finally:
            self.finished.emit()

    def _progress_callback(self, message: str):
        """進捗メッセージを受信してシグナルを発行"""
        self.progress_updated.emit(message)

    def get_result(self) -> T | None:
        """実行結果を取得"""
        return self._result

    def get_error(self) -> Exception | None:
        """発生したエラーを取得"""
        return self._error

