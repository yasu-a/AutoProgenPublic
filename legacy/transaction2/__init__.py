import threading
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Generic, Callable, Hashable, NamedTuple, TypeVar
from uuid import UUID, uuid4

from PyQt5.QtCore import QMutex, QThread

from domain.models.values import StudentID, TestCaseID, StorageID


class ThreadID(NamedTuple):
    py_thread_id: int
    qt_thread_id: int

    @classmethod
    def get_current(cls):
        return cls(
            py_thread_id=threading.get_ident(),
            qt_thread_id=int(QThread.currentThreadId()),
        )


def _get_thread_id() -> ThreadID:
    return ThreadID.get_current()


class TransactionID(NamedTuple):
    uuid: UUID

    @classmethod
    def create_instance(cls):
        return cls(uuid=uuid4())


class TransactionServer:
    def __init__(self):
        self._active_tx_id_mapping: dict[ThreadID, TransactionID] = {}

    def get_transaction_id(self) -> TransactionID:
        # @transactionalデコレータが張ってある関数に入った時に，トランザクションIDを生成する
        thread_id = _get_thread_id()
        active_tx_id = self._active_tx_id_mapping.get(thread_id)
        if active_tx_id is not None:
            # スレッド内ですでにトランザクションが張られている場合
            return self._active_tx_id_mapping[thread_id]
        else:
            # スレッド内でまだトランザクションが張られていない場合
            new_tx_id = TransactionID.create_instance()
            self._active_tx_id_mapping[thread_id] = new_tx_id
            return new_tx_id


class LockMode(Enum):
    READONLY = 1
    WRITABLE = 2


class ResourceOwner(NamedTuple):
    owner_tx_id: TransactionID


class ResourceOwnerModeMapping:
    def __init__(self):
        self._readonly_owners: set[ResourceOwner] = set()
        self._writable_owners: set[ResourceOwner] = set()

    def __setitem__(self, owner: ResourceOwner, mode: LockMode):
        if mode == LockMode.READONLY:
            if owner in self._readonly_owners:
                raise ValueError("Owner requests multiple lock modes", owner, mode)
            self._readonly_owners.add(owner)
        elif mode == LockMode.WRITABLE:
            if owner in self._writable_owners:
                raise ValueError("Owner requests multiple lock modes", owner, mode)
            self._writable_owners.add(owner)
        else:
            assert False, owner

    def has_readonly(self) -> bool:
        return len(self._readonly_owners) > 0

    def has_writable(self) -> bool:
        return len(self._writable_owners) > 0

    def contains_in_readonly(self, owner: ResourceOwner):
        return owner in self._readonly_owners

    def contains_in_writable(self, owner: ResourceOwner):
        return owner in self._writable_owners

    def get(self, owner: ResourceOwner) -> LockMode | None:
        if owner in self._readonly_owners:
            return LockMode.READONLY
        elif owner in self._writable_owners:
            return LockMode.WRITABLE
        else:
            return None


ResourceID = StudentID | TestCaseID | StorageID


class LockServer:
    def __init__(self):
        self._lock = QMutex()
        self._global_locks: dict[type[ResourceID], ResourceOwnerModeMapping] \
            = defaultdict(ResourceOwnerModeMapping)
        self._local_locks: dict[ResourceID, ResourceOwnerModeMapping] \
            = defaultdict(ResourceOwnerModeMapping)

    @contextmanager
    def __lock(self):
        self._lock.lock()
        try:
            yield
        finally:
            self._lock.unlock()

    def try_acquire_global_readonly_lock(
            self,
            *,
            owner: ResourceOwner,
            rid_type: type[ResourceID],
    ) -> bool:
        # リエントラントを考慮して，リソース全体に対する読み取り専用ロックの取得を試みる
        # リソース全体のすべてのIDに書きこみ可能ロックが取得されていない場合に取得できる
        # リソース全体に対して書き込み可能ロック・読み取り専用ロックが取得されている場合は何もしない

        with (self.__lock()):
            for rid, owner_set in self._local_locks.items():
                if not isinstance(rid, rid_type):
                    continue
                if owner_set.has_writable():
                    # もし書き込み可能ロックが取得されているなら
                    if owner_set.contains_in_writable(owner):
                        # 自分がロックを所有していたらロックできる
                        pass
