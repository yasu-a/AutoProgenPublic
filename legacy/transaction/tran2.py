import threading
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Generic, Callable, Hashable, NamedTuple, TypeVar
from uuid import UUID

from PyQt5.QtCore import QMutex, QThread

from domain.models.values import StudentID, TestCaseID


class ThreadID(NamedTuple):
    py_thread_id: int
    qt_thread_id: int

    @classmethod
    def get_current(cls):
        return cls(
            py_thread_id=threading.get_ident(),
            qt_thread_id=int(QThread.currentThreadId()),
        )


ResourceID = Hashable  # ID type
I = TypeVar("I", bound=ResourceID)  # ID type


class LockMode(Enum):
    READONLY = 1
    WRITABLE = 2


@dataclass(frozen=True)
class LockRequest:
    id_value: ResourceID | None
    mode: LockMode

    @property
    def is_global(self) -> bool:
        return self.id_value is None


class TransactionID(NamedTuple):
    uuid: UUID


class LockKey(NamedTuple):
    resource_id: ResourceID


class LockOwner(NamedTuple):
    transaction_id: TransactionID
    mode: LockMode


@dataclass(slots=False)
class LockItem:
    lock: QMutex
    owners: set[LockOwner]


class LockServer:
    def __init__(self):
        self._locks: dict[LockKey, LockItem] = {}

    def



class AbstractLockState(ABC):
    @abstractmethod
    def enter(self, id_value: I | None) -> None:
        raise NotImplementedError()

    @abstractmethod
    def leave(self, id_value: I | None) -> None:
        raise NotImplementedError()

    @abstractmethod
    def is_entered(self, id_value: I | None) -> bool:
        raise NotImplementedError()


class LocalLockState(AbstractLockState):
    def __init__(self):
        self._counts: dict[I, int] = defaultdict(int)

    def enter(self, id_value: I | None) -> None:
        assert id_value is not None
        self._counts[id_value] += 1

    def leave(self, id_value: I | None) -> None:
        assert id_value is not None
        self._counts[id_value] -= 1

    def is_entered(self, id_value: I | None) -> bool:
        assert id_value is not None
        return self._counts[id_value] > 0


class GlobalLockState(AbstractLockState):
    def __init__(self):
        self._flag: bool = False

    def enter(self, id_value: I | None) -> None:
        assert id_value is None
        self._flag = True

    def leave(self, id_value: I | None) -> None:
        assert id_value is not None
        self._flag = False

    def is_entered(self, id_value: I | None) -> bool:
        assert id_value is not None
        return self._flag


class ReadWriteLockState:
    # * データ構造
    #   - 読み込みlocal-lock Lr(r): IDType -> int([0, inf))
    #   - 読み込みglobal-lock Gr: int([0, inf))
    #   - 書き込みlocal-lock Lw(r): IDType -> bool
    #   - 書き込みglobal-lock Gw: bool
    # * 手続き
    #   - リソースrに対する読み取り専用local-lock
    #     - 取得条件: not Lw(r) and not Gw
    #     - 取得操作: Lr(r) += 1; Gr += 1
    #     - 解放操作: Lr(r) -= 1; Gr -= 1
    #   - 読み取り専用global-lock
    #     - 取得条件: not Gw
    #     - 取得操作: Gr += 1
    #     - 解放操作: Gr -= 1
    #   - リソースrに対する書き込み可能local-lock
    #     - 取得条件: not Lw(r) and not Gw and Lr(r) != 0 and Gr != 0
    #     - 取得操作: Lw(r) = True; Gw = True
    #     - 解放操作: Lw(r) = False; Gw = False
    #   - 書き込み可能global-lock
    #     - 取得条件: not Gw
    #     - 取得操作: Gw = True
    #     - 解放操作: Gw = False

    def __init__(self):
        self._local_write_ls = LocalLockState()
        self._local_read_ls = LocalLockState()
        self._global_write_ls = GlobalLockState()
        self._global_read_ls = GlobalLockState()

    def is_readonly_local_lock_acquirable(self, id_value: I) -> bool:
        if self._local_write_ls.is_entered(id_value):
            return False
        if self._global_write_ls.is_entered(id_value):
            return False
        return True

    def acquire_readonly_local_lock(self, id_value: I) -> None:
        self._local_read_ls.enter(id_value)
        self._global_read_ls.enter(None)

    def release_readonly_local_lock(self, id_value: I) -> None:
        self._local_read_ls.leave(id_value)
        self._global_read_ls.leave(None)

    def is_readonly_global_lock_acquirable(self) -> bool:
        if self._global_write_ls.is_entered(None):
            return False
        return True

    def acquire_readonly_global_lock(self) -> None:
        self._global_read_ls.enter(None)

    def release_readonly_global_lock(self) -> None:
        self._global_read_ls.leave(None)

    def is_writable_local_lock_acquirable(self, id_value: I) -> bool:
        if self._local_write_ls.is_entered(id_value):
            return False
        if self._global_write_ls.is_entered(None):
            return False
        if self._local_read_ls.is_entered(id_value):
            return False
        if self._global_read_ls.is_entered(None):
            return False
        return True

    def acquire_writable_local_lock(self, id_value: I) -> None:
        self._local_write_ls.enter(id_value)
        self._global_write_ls.enter(None)

    def release_writable_local_lock(self, id_value: I) -> None:
        self._local_write_ls.leave(id_value)
        self._global_write_ls.leave(None)

    def is_writable_global_lock(self) -> bool:
        if self._global_write_ls.is_entered(None):
            return False
        return True

    def acquire_writable_global_lock(self) -> None:
        self._global_write_ls.enter(None)

    def release_writable_global_lock(self) -> None:
        self._global_write_ls.leave(None)


@dataclass(frozen=True)
class LockTicket:
    req: LockRequest


class ResourceLockServer(Generic[I]):
    # 次のロックを管理する
    #  - global-lock：リソースの集合（student_id全体）に対するロック
    #  - local-lock：個々のリソース（あるstudent_id）に対するロック
    # * リエントラント可能性
    #  - 同じトランザクション内で既に取得されているlockのsubsetにあたるlockを取得すること
    #  - 既に書き込み可能lockが取得されているときは，自由にリエントラントできる
    #  - 既に読み込み可能lockが取得されているときに書きこみ可能lockを取得するときは昇格する
    #    - 昇格
    # * 仕様
    #   - あるリソースrに対するlocal-lockががかかっているかどうか = local-lockとglobal-lockがかかっていない
    #   - 読み取り専用local-lockは，書き込みに関するlocal-lockがかかっていなければ取得できる
    #   - 読み取り専用global-lockは，書き込みに関するglobal-lockがかかっていなければ取得できる
    #   - 書き込み可能local-lockは，読み込みと書きこみ両方に関するlocal-lockがかかっていなければ取得できる
    #   - 書き込み可能global-lockは，読み込みと書きこみ両方に関するglobal-lockがかかっていなければ取得できる
    # * 実装はReadWriteLockStateを参照

    def __init__(self):
        self._lock = QMutex()
        self._lock_state = ReadWriteLockState()

    @contextmanager
    def __lock(self):
        self._lock.lock()
        try:
            yield
        finally:
            self._lock.unlock()

    def __block_until_predicate_then_run_command_atomic(
            self,
            *,
            predicate: Callable[[], bool],
            command: Callable[[], None],
    ) -> None:
        while True:
            with self.__lock():
                if predicate():
                    command()
                    break
            time.sleep(0.01)

    def _lock_impl(self, mode: LockMode, id_value: I | None) -> None:
        if mode == LockMode.READONLY and id_value is not None:
            self.__block_until_predicate_then_run_command_atomic(
                predicate=lambda: self._lock_state.is_readonly_local_lock_acquirable(id_value),
                command=lambda: self._lock_state.acquire_readonly_local_lock(id_value),
            )
        elif mode == LockMode.READONLY and id_value is None:
            self.__block_until_predicate_then_run_command_atomic(
                predicate=self._lock_state.is_readonly_global_lock_acquirable,
                command=self._lock_state.acquire_readonly_global_lock,
            )
        elif mode == LockMode.WRITABLE and id_value is not None:
            self.__block_until_predicate_then_run_command_atomic(
                predicate=lambda: self._lock_state.is_writable_local_lock_acquirable(id_value),
                command=lambda: self._lock_state.acquire_writable_local_lock(id_value),
            )
        elif mode == LockMode.WRITABLE and id_value is None:
            self.__block_until_predicate_then_run_command_atomic(
                predicate=self._lock_state.is_writable_global_lock,
                command=self._lock_state.acquire_writable_global_lock,
            )
        else:
            assert False, (mode, id_value)

    def lock(self, req: LockRequest) -> LockTicket:
        self._lock_impl(req.mode, req.id_value)
        return LockTicket(  # TODO: 本当はチケットの発行を管理したい
            req=req,
        )

    def __run_command_atomic(
            self,
            *,
            command: Callable[[], None],
    ) -> None:
        with self.__lock():
            command()

    def _unlock_impl(self, mode: LockMode, id_value: I | None) -> None:
        if mode == LockMode.READONLY and id_value is not None:
            self.__run_command_atomic(
                command=lambda: self._lock_state.release_readonly_local_lock(id_value),
            )
        elif mode == LockMode.READONLY and id_value is None:
            self.__run_command_atomic(
                command=self._lock_state.release_readonly_global_lock,
            )
        elif mode == LockMode.WRITABLE and id_value is not None:
            self.__run_command_atomic(
                command=lambda: self._lock_state.release_writable_local_lock(id_value),
            )
        elif mode == LockMode.WRITABLE and id_value is None:
            self.__run_command_atomic(
                command=self._lock_state.release_writable_global_lock,
            )
        else:
            assert False, (mode, id_value)

    def unlock(self, ticket: LockTicket) -> None:
        req = ticket.req
        self._unlock_impl(req.mode, req.id_value)


class LockServerFactory:
    def __init__(self):
        self._servers = {
            StudentID: ResourceLockServer(),
            TestCaseID: ResourceLockServer(),
        }

    def __getitem__(self, id_type: type[I]) -> ResourceLockServer:
        return self._servers[id_type]


_lock_server_factory = LockServerFactory()


def get_lock_server_factory(id_type: type[I]) -> ResourceLockServer:
    return _lock_server_factory[id_type]
