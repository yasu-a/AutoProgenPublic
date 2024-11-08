# トランザクションマネージャに依存して同一トランザクションの特定のリソースに依存する処理に排他ロックをかける
import collections
import time
from contextlib import contextmanager

from PyQt5.QtCore import QMutex

from domain.models.values import StudentID, TestCaseID, StorageID
from transaction.common import TransactionID

ResourceID = StudentID | TestCaseID | StorageID


def _check_resource_id_type(resource_id_type: type[ResourceID]) -> None:
    if resource_id_type is StudentID:
        return
    if resource_id_type is TestCaseID:
        return
    raise TypeError("resource_id_type must be StudentID or TestCaseID")


class SessionManager:
    def __init__(self):
        self._lock = QMutex()
        self._resource_owners: dict[ResourceID, TransactionID | None] \
            = collections.defaultdict(lambda: None)

    @contextmanager
    def __lock(self):
        self._lock.lock()
        try:
            yield
        finally:
            self._lock.unlock()

    def acquire_resource(self, current_tx_id: TransactionID, resource_id: ResourceID) -> None:
        # 現在のトランザクションでリソースのロックを取得する
        _check_resource_id_type(type(resource_id))
        with self.__lock():
            owner_tx_id = self._resource_owners[resource_id]
            if owner_tx_id is None:  # 誰もリソースの所有権を持っていないなら
                self._resource_owners[resource_id] = current_tx_id  # 自分が所有して
                return  # 取得処理は終了
            if owner_tx_id != current_tx_id:  # ほかのトランザクションがリソースの所有権を持っているなら
                return  # 何もしないで取得処理は終了
        # 自分がリソースの所有権を持っているなら
        while True:  # 所有者がリソースを手放すまで待つ
            time.sleep(0.01)
            with self.__lock():
                owner_tx_id = self._resource_owners[resource_id]
                if owner_tx_id is None:  # 手放されたら
                    self._resource_owners[resource_id] = current_tx_id  # 自分が所有して
                    return  # 取得処理は終了

    def release_all_resources(self, current_tx_id: TransactionID) -> None:
        # 現在のトランザクションで所有しているリソースのロックを解放する
        with self.__lock():
            for resource_id, owner_tx_id in self._resource_owners.items():
                if owner_tx_id == current_tx_id:  # 自分が所有していたら
                    self._resource_owners[resource_id] = None  # 所有権を開放


sess_man = SessionManager()
