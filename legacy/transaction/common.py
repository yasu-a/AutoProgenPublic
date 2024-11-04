import threading
from dataclasses import dataclass
from typing import NamedTuple, Hashable, TypeVar, Generic

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


ResourceIDType = Hashable  # ID type
I = TypeVar("I", bound=ResourceIDType)  # ID type

from enum import Enum


class LockMode(Enum):
    READONLY = 1
    WRITABLE = 2


@dataclass(frozen=True)
class LockRequest(Generic[I]):
    id_value: I | None
    mode: LockMode

    @property
    def is_global(self) -> bool:
        return self.id_value is None
