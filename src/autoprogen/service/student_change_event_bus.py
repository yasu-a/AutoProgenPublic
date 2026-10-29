from collections.abc import Callable
from threading import Lock

from autoprogen.domain.model.value import StudentID
from autoprogen.util.app_logging import create_logger


class StudentChangeEventBus:
    """プロジェクト内の学生データ変更を学生IDごとに購読者へ通知する。"""

    def __init__(self) -> None:
        """購読管理用の状態とロックを初期化する。"""
        self._lock = Lock()
        self._next_subscription_id = 0
        self._subscribers_by_student: dict[
            StudentID, dict[int, Callable[[StudentID], None]]
        ] = {}
        self._student_by_subscription: dict[int, StudentID] = {}
        self._logger = create_logger()

    def subscribe(self, student_id: StudentID, callback: Callable[[StudentID], None]) -> int:
        """学生の変更を購読し、解除に使うIDを返す。"""
        with self._lock:
            subscription_id = self._next_subscription_id
            self._next_subscription_id += 1
            self._subscribers_by_student.setdefault(student_id, {})[subscription_id] = callback
            self._student_by_subscription[subscription_id] = student_id
        return subscription_id

    def unsubscribe(self, subscription_id: int) -> None:
        """購読を解除する。既に解除済みの場合は何もしない。"""
        with self._lock:
            student_id = self._student_by_subscription.pop(subscription_id, None)
            if student_id is None:
                return
            subscribers = self._subscribers_by_student[student_id]
            del subscribers[subscription_id]
            if not subscribers:
                del self._subscribers_by_student[student_id]

    def notify(self, student_id: StudentID) -> None:
        """対象学生の購読者へ通知し、購読者の失敗を保存処理へ伝播させない。"""
        with self._lock:
            callbacks = tuple(self._subscribers_by_student.get(student_id, {}).values())

        # コールバックはロック外で実行し、通知中の購読変更を妨げない。
        for callback in callbacks:
            try:
                callback(student_id)
            except Exception:
                self._logger.exception("Student change subscriber failed: %s", student_id)
