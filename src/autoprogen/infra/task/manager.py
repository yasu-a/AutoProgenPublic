import time
from contextlib import contextmanager
from PyQt5.QtCore import QObject, QTimer, QMutex, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import qApp

from autoprogen.infra.repository.global_settings import GlobalSettingsRepository
from autoprogen.infra.task.queue import AbstractTaskQueue, StudentTaskQueue
from autoprogen.infra.task.task import AbstractTask, AbstractStudentTask
from autoprogen.usecase.progress import ProgressCallback
from autoprogen.util.app_logging import create_logger


class _TaskStack:
    # thread-unsafe

    def __init__(self):
        self._task_queues: dict[str, AbstractTaskQueue] = {}

    def register_task_queue(self, name: str, task_queue: AbstractTaskQueue):
        assert name not in self._task_queues
        self._task_queues[name] = task_queue

    def count(self) -> int:
        count = 0
        for task_queue in self._task_queues.values():
            count += task_queue.count()
        return count

    def count_active(self) -> int:
        count = 0
        for task_queue in self._task_queues.values():
            count += task_queue.count_active()
        return count

    def is_empty(self) -> bool:
        for task_queue in self._task_queues.values():
            if not task_queue.is_empty():
                return False
        return True

    def enqueue(self, name: str, task: AbstractTask) -> None:
        self._task_queues[name].enqueue(task)

    def list_unstarted_tasks(self, n_max: int) -> list[AbstractTask]:
        unstarted_tasks: list[AbstractTask] = []
        for task_queue in self._task_queues.values():
            for task in task_queue.iter_unstarted():
                if len(unstarted_tasks) >= n_max:
                    return unstarted_tasks
                unstarted_tasks.append(task)
        return unstarted_tasks

    def list_active_tasks(self) -> list[AbstractTask]:
        active_tasks: list[AbstractTask] = []
        for task_queue in self._task_queues.values():
            for task in task_queue.iter_active():
                active_tasks.append(task)
        return active_tasks

    def dequeue_finished_tasks(self) -> None:
        for task_queue in self._task_queues.values():
            tasks_to_dequeue = []
            for task in task_queue.iter_finished():
                tasks_to_dequeue.append(task)
            for task in tasks_to_dequeue:
                task_queue.dequeue(task)

    def dequeue_unstarted_tasks(self) -> None:
        for task_queue in self._task_queues.values():
            tasks_to_dequeue = []
            for task in task_queue.iter_unstarted():
                tasks_to_dequeue.append(task)
            for task in tasks_to_dequeue:
                task_queue.dequeue(task)

    def send_stop_to_all_tasks(self) -> None:
        for task_queue in self._task_queues.values():
            for task in task_queue.iter_all():
                task.send_stop()


class TaskManager(QObject):
    # thread-safe

    busy_changed = pyqtSignal(bool)
    _logger = create_logger()

    def __init__(self, global_settings_repo: GlobalSettingsRepository):
        super().__init__(qApp)

        self._max_workers = global_settings_repo.get().max_workers

        self.__stack = _TaskStack()
        self.__stack.register_task_queue("student", StudentTaskQueue())

        self.__timer = QTimer()
        self.__timer.setInterval(100)
        self.__timer.timeout.connect(self.__timer_timeout)  # type: ignore
        self.__timer.start()

        self.__lock = QMutex()
        self.__last_busy = False

    @contextmanager
    def _lock(self):
        self.__lock.lock()
        try:
            yield
        finally:
            self.__lock.unlock()

    def _capture_busy_transition_locked(self) -> bool | None:
        """ロック保持中に空・非空の遷移を検出し、通知する値を返す。"""
        current_busy = not self.__stack.is_empty()
        if current_busy == self.__last_busy:
            return None
        self.__last_busy = current_busy
        return current_busy

    def count(self):
        with self._lock():
            return self.__stack.count()

    def count_active(self):
        with self._lock():
            return self.__stack.count_active()

    def is_empty(self):
        with self._lock():
            return self.__stack.is_empty()

    def enqueue(self, task: AbstractTask):
        """タスクを登録し、最初の1件でbusyをロック外通知する。"""
        transition: bool | None = None
        with self._lock():
            if isinstance(task, AbstractStudentTask):
                self.__stack.enqueue("student", task)
            else:
                assert False, task
            transition = self._capture_busy_transition_locked()
        # QtのスロットがTaskManagerを再参照できるよう、ロック外で通知する。
        if transition is not None:
            self.busy_changed.emit(transition)

    @pyqtSlot()
    def __timer_timeout(self):
        """未開始のタスクを開始し、完了除去後のbusy遷移を通知する。"""
        transition: bool | None = None
        with self._lock():
            # 未開始のタスクの開始
            n_max = max(self._max_workers - self.__stack.count_active(), 0)
            unstarted_tasks = self.__stack.list_unstarted_tasks(n_max)
            for task in unstarted_tasks:
                task.start()
                self._logger.info(f"Task started: {task}")

            # 終了したタスクの削除
            self.__stack.dequeue_finished_tasks()
            transition = self._capture_busy_transition_locked()
        if transition is not None:
            self.busy_changed.emit(transition)

    def terminate(self, progress_callback: ProgressCallback | None = None):
        """登録済みタスクの停止を待ち、キューが空になったら通知する。"""
        while True:
            # メッセージ
            with self._lock():
                n_tasks = self.__stack.count()
                active_tasks = self.__stack.list_active_tasks()
                self._logger.info(
                    f"Waiting {n_tasks} tasks to finish\n"
                    + "\n".join(f" - {task!r}" for task in active_tasks),
                )
                # TODO: usecase layer
                if progress_callback is not None:
                    progress_callback(
                        f"{n_tasks}個のタスクが終了するのを待っています・・・\n"
                        + "\n".join(f" - {task!s}" for task in active_tasks[:8]),
                    )
            with self._lock():
                # 新たなタスクが開始しないように未開始のタスクを消す
                self.__stack.dequeue_unstarted_tasks()
                # すべてのタスクに終了シグナルを送る
                self.__stack.send_stop_to_all_tasks()
            # 少し待つ
            time.sleep(0.1)
            transition: bool | None = None
            with self._lock():
                # 終了したタスクの削除
                self.__stack.dequeue_finished_tasks()
                # タスクが終了しているかを確認
                n_tasks = self.__stack.count()
                transition = self._capture_busy_transition_locked()
            if transition is not None:
                self.busy_changed.emit(transition)
            if n_tasks == 0:
                break
            # 少し待つ
            time.sleep(0.1)
