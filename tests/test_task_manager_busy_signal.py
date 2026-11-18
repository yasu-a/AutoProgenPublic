"""TaskManagerのキュー空・非空の遷移通知を検証する。"""

from threading import Thread, get_ident
from unittest.mock import Mock

import pytest
from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWidgets import QApplication

from autoprogen.domain.model.value import StudentID
from autoprogen.infra.task.manager import TaskManager
from autoprogen.infra.task.task import AbstractStudentTask


@pytest.fixture
def qt_app(monkeypatch: pytest.MonkeyPatch) -> QApplication:
    """QtのSignalが受信できるアプリケーションを返す。"""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def manager(qt_app: QApplication):
    """実時間タイマーを停止したTaskManagerを生成する。"""
    settings_repo = Mock()
    settings_repo.get.return_value.max_workers = 2
    task_manager = TaskManager(settings_repo)
    task_manager._TaskManager__timer.stop()
    yield task_manager
    task_manager._TaskManager__timer.stop()
    task_manager.deleteLater()


def _task(student_number: str) -> Mock:
    """QThreadを起動せず状態だけ切り替えられる学生タスクを返す。"""
    task = Mock(spec=AbstractStudentTask)
    task.student_id = StudentID(student_number)
    task.isRunning.return_value = False
    task.isFinished.return_value = False

    def start_task() -> None:
        """開始状態をMockへ反映する。"""
        task.isRunning.return_value = True

    task.start.side_effect = start_task
    return task


def test_enqueue_emits_true_immediately_once(manager: TaskManager) -> None:
    """1件目のenqueueで即時True、その後の追加では重複しない。"""
    signals: list[bool] = []
    manager.busy_changed.connect(signals.append)
    assert manager.is_empty()

    manager.enqueue(_task("21D5109047B"))
    assert signals == [True]
    manager.enqueue(_task("21D5109048C"))
    assert signals == [True]


def test_finishing_last_task_emits_false_once(manager: TaskManager) -> None:
    """一部終了時はbusy維持、最後の完了除去でFalseを一度だけ通知する。"""
    signals: list[bool] = []
    manager.busy_changed.connect(signals.append)
    first = _task("21D5109047B")
    second = _task("21D5109048C")
    manager.enqueue(first)
    manager.enqueue(second)
    manager._TaskManager__timer_timeout()

    first.isRunning.return_value = False
    first.isFinished.return_value = True
    manager._TaskManager__timer_timeout()
    assert signals == [True]
    assert not manager.is_empty()

    second.isRunning.return_value = False
    second.isFinished.return_value = True
    manager._TaskManager__timer_timeout()
    manager._TaskManager__timer_timeout()
    assert signals == [True, False]
    assert manager.is_empty()


def test_failed_enqueue_does_not_notify_twice(manager: TaskManager) -> None:
    """同じ学生を重複登録して失敗した場合も通知状態を変えない。"""
    signals: list[bool] = []
    manager.busy_changed.connect(signals.append)
    student_id = "21D5109047B"
    manager.enqueue(_task(student_id))
    with pytest.raises(AssertionError):
        manager.enqueue(_task(student_id))
    assert signals == [True]


class _GuiReceiver(QObject):
    """受信された通知の値とスレッドを記録する。"""

    def __init__(self) -> None:
        """空の通知履歴を作る。"""
        super().__init__()
        self.signals: list[tuple[bool, int]] = []

    @pyqtSlot(bool)
    def receive(self, is_busy: bool) -> None:
        """Signalを受信したスレッドIDを記録する。"""
        self.signals.append((is_busy, get_ident()))


def test_terminate_notifies_gui_thread(
        manager: TaskManager,
        qt_app: QApplication,
) -> None:
    """別スレッドから停止してもQtがGUIスレッドへ通知を配送する。"""
    first = _task("21D5109047B")
    manager.enqueue(first)
    first.isRunning.return_value = False
    first.isFinished.return_value = True
    receiver = _GuiReceiver()
    manager.busy_changed.connect(receiver.receive)
    worker = Thread(target=manager.terminate)
    worker.start()
    worker.join(timeout=3)
    assert not worker.is_alive()
    qt_app.processEvents()
    assert receiver.signals == [(False, get_ident())]
