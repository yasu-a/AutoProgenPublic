from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Iterable

from domain.models.values import StudentID
from infra.tasks.task import AbstractTask, AbstractStudentTask

T = TypeVar("T", bound=AbstractTask)


class AbstractTaskQueue(ABC, Generic[T]):
    @abstractmethod
    def iter_unstarted(self) -> Iterable[T]:
        # キューの開始されていないタスクをイテレートする
        raise NotImplementedError()

    @abstractmethod
    def iter_active(self) -> Iterable[T]:
        # キューの実行中のタスクをイテレートする
        raise NotImplementedError()

    @abstractmethod
    def iter_finished(self) -> Iterable[T]:
        # キューの終了したタスクをイテレートする
        raise NotImplementedError()

    @abstractmethod
    def iter_all(self) -> Iterable[T]:
        # すべてのタスクをイテレートする
        raise NotImplementedError()

    def count(self) -> int:
        # キュー内のすべてのタスクの数を数える
        return sum(1 for _ in self.iter_all())

    def count_active(self) -> int:
        # キュー内で実行中のタスクの数を数える
        return sum(1 for _ in self.iter_active())

    def is_empty(self) -> bool:
        # キュー内で実行中のタスクが存在するか検証する（高速な実装）
        for _ in self.iter_all():
            return False
        return True

    @abstractmethod
    def enqueue(self, task: T) -> None:
        # キューにタスクを追加する
        raise NotImplementedError()

    @abstractmethod
    def dequeue(self, task: T) -> None:
        # タスクを消す
        raise NotImplementedError()


class StudentTaskQueue(AbstractTaskQueue[AbstractStudentTask]):
    def __init__(self):
        self._q: dict[StudentID, AbstractStudentTask] = {}

    def iter_unstarted(self) -> Iterable[AbstractStudentTask]:
        for task in self._q.values():
            if not task.isRunning() and not task.isFinished():
                yield task

    def iter_active(self) -> Iterable[AbstractStudentTask]:
        for task in self._q.values():
            if task.isRunning():
                yield task

    def iter_finished(self) -> Iterable[AbstractStudentTask]:
        for task in self._q.values():
            if task.isFinished():
                yield task

    def iter_all(self) -> Iterable[T]:
        for task in self._q.values():
            yield task

    def enqueue(self, task: AbstractStudentTask) -> None:
        assert task.student_id not in self._q
        self._q[task.student_id] = task

    def dequeue(self, task: AbstractStudentTask) -> None:
        del self._q[task.student_id]
