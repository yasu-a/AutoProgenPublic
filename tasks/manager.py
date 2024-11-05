from contextlib import contextmanager
from typing import Iterable

from PyQt5.QtCore import QObject, QTimer, QMutex
from PyQt5.QtWidgets import qApp

from domain.models.values import StudentID
from infra.repositories.global_config import GlobalConfigRepository
from tasks.tasks import AbstractStudentTask, AbstractTask
from utils.app_logging import create_logger


class TaskOperationError(RuntimeError):
    def __init__(self, reason: str):
        self.reason = reason


class TaskStack(QObject):
    _logger = create_logger()

    def __init__(self, parent: QObject, max_workers: int):
        super().__init__(parent)

        self._max_workers = max_workers

        self._student_tasks: dict[StudentID, AbstractStudentTask] = {}

        self.__lock = QMutex()

        self._timer = QTimer()
        self._timer.setInterval(10)
        self._timer.timeout.connect(self._timer_timeout)  # type: ignore
        self._timer.start()

    @contextmanager
    def _lock(self):
        self.__lock.lock()
        try:
            yield
        finally:
            self.__lock.unlock()

    def enqueue_student_task(self, student_task: AbstractStudentTask):
        assert isinstance(student_task, AbstractStudentTask), student_task
        if student_task.student_id in self._student_tasks.keys():
            raise TaskOperationError(
                reason=f"学籍番号{student_task}にはすでに実行中のタスクが存在します"
            )
        with self._lock():
            self._student_tasks[student_task.student_id] = student_task

    def _iter_tasks(self, *, task_cls: type = None) -> Iterable[AbstractTask]:
        def iter_all():
            yield from self._student_tasks.values()

        for task in iter_all():
            if task_cls is not None:
                if isinstance(task, task_cls):
                    yield task
            else:
                yield task

    def _pop_task(self, task_to_be_deleted: AbstractTask) -> None:
        for student_id, student_task in self._student_tasks.items():
            if task_to_be_deleted is student_task:
                self._student_tasks.pop(student_id)
                return

    def _get_task_count(self, *, task_cls: type = None) -> int:
        return len(list(self._iter_tasks(task_cls=task_cls)))

    def _get_running_task_count(self) -> int:
        return sum([task.isRunning() for task in self._iter_tasks()])

    def _timer_timeout(self):
        with self._lock():
            # 終了したタスクをプールから削除
            tasks_to_be_deleted = []
            for task in self._iter_tasks():
                if task.isFinished():
                    tasks_to_be_deleted.append(task)
            for task in tasks_to_be_deleted:
                self._pop_task(task)

            # プールを満たすまでタスクをスタートする
            n_tasks_to_start = self._max_workers - self._get_running_task_count()
            if n_tasks_to_start <= 0:
                return
            started_task_count = 0
            for task in self._iter_tasks():
                if n_tasks_to_start <= started_task_count:
                    break
                if not task.isRunning():
                    # self._logger.debug(f"Task {task} started")
                    task.start()
                    started_task_count += 1

    def get_task_count(self, *, task_cls: type = None) -> int:
        with self._lock():
            return self._get_task_count(task_cls=task_cls)

    def get_running_task_count(self) -> int:
        with self._lock():
            return self._get_running_task_count()

    def kill_all(self) -> None:
        with self._lock():
            for task in list(self._iter_tasks()):
                task.terminate()
                task.wait()
                self._pop_task(task)


class TaskManager(QObject):
    def __init__(self, global_settings_repo: GlobalConfigRepository):
        super().__init__(qApp)

        self._task_stack = TaskStack(
            parent=self,
            max_workers=global_settings_repo.get().max_workers,
        )

    def enqueue_student_task(self, student_task: AbstractStudentTask) -> None:
        self._task_stack.enqueue_student_task(student_task)

    def get_task_count(self) -> int:
        return self._task_stack.get_task_count()

    def get_student_task_count(self) -> int:
        return self._task_stack.get_task_count(task_cls=AbstractStudentTask)

    def get_running_task_count(self) -> int:
        return self._task_stack.get_running_task_count()

    def kill_all_tasks(self) -> None:
        # FIXME: タスクにstop_producerを追加，すべてのタスク実装に反映して安全にプロセスを終了する仕組みを作る
        self._task_stack.kill_all()

    def terminate(self):
        self.kill_all_tasks()
