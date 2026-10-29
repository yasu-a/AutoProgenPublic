from threading import Lock

from PyQt5.QtCore import QObject, QTimer, Qt, pyqtSignal, pyqtSlot

from autoprogen.domain.model.value import StudentID
from autoprogen.service.student_change_event_bus import StudentChangeEventBus


class QtStudentChangeBridge(QObject):
    """Qt非依存の学生変更通知をGUIスレッドのシグナルへ橋渡しする。"""

    _COALESCE_INTERVAL_MS = 20
    _delivery_requested = pyqtSignal(StudentID)
    student_changed = pyqtSignal(StudentID)

    def __init__(
            self,
            parent: QObject,
            *,
            student_ids: list[StudentID],
            student_change_event_bus: StudentChangeEventBus,
    ) -> None:
        """表示中の学生を購読し、GUIスレッドでの通知配送を準備する。"""
        super().__init__(parent)
        self._student_change_event_bus = student_change_event_bus
        self._lock = Lock()
        self._stopped = False
        self._pending_student_ids: dict[StudentID, None] = {}
        self._subscribed_student_ids: set[StudentID] = set()

        self._flush_timer = QTimer(self)
        self._flush_timer.setSingleShot(True)
        self._flush_timer.timeout.connect(self._flush_pending)
        self._delivery_requested.connect(self._on_delivery_requested, Qt.QueuedConnection)

        self._subscription_ids: list[int] = []
        self.set_student_ids(student_ids)

    def set_student_ids(self, student_ids: list[StudentID]) -> None:
        """全件ロード後の学生一覧に合わせて購読対象を更新する。"""
        self._subscribed_student_ids = set(student_ids)
        self._pending_student_ids = {
            student_id: None
            for student_id in self._pending_student_ids
            if student_id in self._subscribed_student_ids
        }
        for subscription_id in self._subscription_ids:
            self._student_change_event_bus.unsubscribe(subscription_id)
        self._subscription_ids = [
            self._student_change_event_bus.subscribe(student_id, self._request_delivery)
            for student_id in student_ids
        ]

    def _request_delivery(self, student_id: StudentID) -> None:
        """任意のスレッドから受けた通知をQtのイベントキューへ送る。"""
        with self._lock:
            if self._stopped:
                return
            self._delivery_requested.emit(student_id)

    @pyqtSlot(StudentID)
    def _on_delivery_requested(self, student_id: StudentID) -> None:
        """GUIスレッドで学生IDを蓄積し、短い間隔の通知をまとめる。"""
        if self._stopped or student_id not in self._subscribed_student_ids:
            return
        self._pending_student_ids[student_id] = None
        if not self._flush_timer.isActive():
            self._flush_timer.start(self._COALESCE_INTERVAL_MS)

    @pyqtSlot()
    def _flush_pending(self) -> None:
        """蓄積した学生IDをそれぞれ一度だけGUIへ通知する。"""
        student_ids = tuple(self._pending_student_ids)
        self._pending_student_ids.clear()
        for student_id in student_ids:
            self.student_changed.emit(student_id)

    def stop(self) -> None:
        """購読を解除し、未配送の通知を破棄する。"""
        with self._lock:
            if self._stopped:
                return
            self._stopped = True

        for subscription_id in self._subscription_ids:
            self._student_change_event_bus.unsubscribe(subscription_id)
        self._subscription_ids.clear()
        self._subscribed_student_ids.clear()
        self._flush_timer.stop()
        self._pending_student_ids.clear()
