from contextlib import contextmanager
from typing import Callable

from PyQt5.QtCore import QMutex

from app_logging import create_logger
from transaction.common import TransactionID


class TransactionManager:
    # システム全体のトランザクションを管理する

    _logger = create_logger()

    def __init__(self):
        self._lock = QMutex()
        # トランザクションID → 同一のトランザクション内で最初にトランザクションを張った関数 のマッピング
        self._transactions: dict[TransactionID: Callable] = {}

    @contextmanager
    def __lock(self):
        self._lock.lock()
        try:
            yield
        finally:
            self._lock.unlock()

    def put_transactional(self, fn: Callable) -> None:
        # トランザクションを張りたい関数を受け取り、トランザクションの管理に追加する
        # 過去にトランザクションを張った関数と同一のトランザクション内にいるべき関数を受け取った時は同一のトランザクションとして管理する
        with self.__lock():
            tx_id = TransactionID.get_current()  # トランザクションIDを取得する
            if tx_id not in self._transactions:  # トランザクションの開始処理をするべきなら
                self._logger.debug(f"TX entered at first time: {fn}")
                self._transactions[tx_id] = fn  # トランザクションを管理に追加する
            else:
                self._logger.debug(f"TX entered again: {fn}")

    def leave_transactional(self, fn: Callable) -> None:
        # トランザクションを張って関数内の処理が実行された後で関数が終了するときに呼び出され、トランザクションの管理終了を処理する
        with self.__lock():
            tx_id = TransactionID.get_current()
            if tx_id in self._transactions:
                if self._transactions[tx_id] is fn:  # トランザクションの終了処理をするべきなら
                    self._logger.debug(f"TX left: {fn}")
                    del self._transactions[tx_id]  # トランザクションを管理から外す
            else:
                raise ValueError("Transaction not entered")

    def get_current(self) -> TransactionID | None:  # トランザクションが張られていない場合はNone
        # 現在のトランザクションIDを返す
        with self.__lock():
            tx_id = TransactionID.get_current()
            return self._transactions.get(tx_id)


tx_man = TransactionManager()
