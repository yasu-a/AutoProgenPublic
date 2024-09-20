import threading
from typing import NamedTuple

from PyQt5.QtCore import QThread


class TransactionID(NamedTuple):
    py_thread_id: int
    qt_thread_id: int

    @classmethod
    def get_current(cls):
        return cls(
            py_thread_id=threading.get_ident(),
            qt_thread_id=int(QThread.currentThreadId()),
        )
