from contextlib import contextmanager

from PyQt5.QtCore import QMutex

from domain.models.values import StudentID


class StudentLockServer:
    def __init__(self):
        self._lock = QMutex()
        self._student_locks: dict[StudentID, QMutex] = {}

    @contextmanager
    def __lock(self):
        self._lock.lock()
        try:
            yield
        finally:
            self._lock.unlock()

    def __getitem__(self, student_id: StudentID) -> QMutex:
        with self.__lock():
            if student_id not in self._student_locks:
                self._student_locks[student_id] = QMutex()
            return self._student_locks[student_id]
