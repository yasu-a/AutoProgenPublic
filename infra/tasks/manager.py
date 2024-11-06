import time
from contextlib import contextmanager
from typing import Callable

from PyQt5.QtCore import QObject, QTimer, QMutex, pyqtSlot
from PyQt5.QtWidgets import qApp

from infra.repositories.global_config import GlobalConfigRepository
from infra.tasks.queue import AbstractTaskQueue, StudentTaskQueue
from infra.tasks.task import AbstractTask, AbstractStudentTask
from utils.app_logging import create_logger


class _TaskStack:
    # thead-unsafe

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
            if task_queue.is_empty():
                return True
        return False

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
    # thead-safe

    _logger = create_logger()

    def __init__(self, global_settings_repo: GlobalConfigRepository):
        super().__init__(qApp)

        self._max_workers = global_settings_repo.get().max_workers

        self.__stack = _TaskStack()
        self.__stack.register_task_queue("student", StudentTaskQueue())

        self.__timer = QTimer()
        self.__timer.setInterval(100)
        self.__timer.timeout.connect(self.__timer_timeout)  # type: ignore
        self.__timer.start()

        self.__lock = QMutex()

    @contextmanager
    def _lock(self):
        self.__lock.lock()
        try:
            yield
        finally:
            self.__lock.unlock()

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
        with self._lock():
            if isinstance(task, AbstractStudentTask):
                self.__stack.enqueue("student", task)
            else:
                assert False, task

    @pyqtSlot()
    def __timer_timeout(self):
        with self._lock():
            # 未開始のタスクの開始
            n_max = max(self._max_workers - self.__stack.count_active(), 0)
            unstarted_tasks = self.__stack.list_unstarted_tasks(n_max)
            for task in unstarted_tasks:
                task.start()
                self._logger.info(f"Task started: {task}")

            # 終了したタスクの削除
            self.__stack.dequeue_finished_tasks()

    def terminate(self, callback: Callable[[str], None]):
        while True:
            # メッセージ
            with self._lock():
                n_tasks = self.__stack.count()
                active_tasks = self.__stack.list_active_tasks()
                self._logger.info(
                    f"Waiting {n_tasks} tasks to finish\n"
                    + "\n".join(f" - {task!r}" for task in active_tasks),
                )
                callback(
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
            with self._lock():
                # 終了したタスクの削除
                self.__stack.dequeue_finished_tasks()
                # タスクが終了しているかを確認
                n_tasks = self.__stack.count()
                if n_tasks == 0:
                    break
            # 少し待つ
            time.sleep(0.1)
