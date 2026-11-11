from concurrent.futures import ThreadPoolExecutor

from autoprogen.service.student_change_event_bus import StudentChangeEventBus
from autoprogen.domain.model.value import StudentID


def test_subscribe_and_unsubscribe_are_scoped_to_student_id() -> None:
    """通知は対象学生の購読者だけへ届き、解除後は届かない。"""
    bus = StudentChangeEventBus()
    first_id = StudentID("21D5109047B")
    second_id = StudentID("26HG209871C")
    received: list[StudentID] = []

    first_subscription = bus.subscribe(first_id, received.append)
    bus.subscribe(second_id, received.append)
    bus.notify(first_id)
    bus.unsubscribe(first_subscription)
    bus.unsubscribe(first_subscription)
    bus.notify(first_id)
    bus.notify(second_id)

    assert received == [first_id, second_id]


def test_subscriber_can_unsubscribe_during_notification() -> None:
    """コールバック中の解除は次回の通知から反映される。"""
    bus = StudentChangeEventBus()
    student_id = StudentID("21D5109047B")
    received: list[StudentID] = []

    def on_change(changed_id: StudentID) -> None:
        """通知を受けた後、自身の購読を解除する。"""
        received.append(changed_id)
        bus.unsubscribe(subscription_id)

    subscription_id = bus.subscribe(student_id, on_change)

    bus.notify(student_id)
    bus.notify(student_id)

    assert received == [student_id]


def test_failing_subscriber_does_not_interrupt_other_subscribers() -> None:
    """購読者の例外で通知元の保存処理を失敗扱いにしない。"""
    bus = StudentChangeEventBus()
    student_id = StudentID("21D5109047B")
    received: list[StudentID] = []

    def fail(_: StudentID) -> None:
        """購読者の失敗を再現する。"""
        raise RuntimeError("subscriber failed")

    bus.subscribe(student_id, fail)
    bus.subscribe(student_id, received.append)

    bus.notify(student_id)

    assert received == [student_id]


def test_notifications_from_multiple_threads() -> None:
    """並列タスクからの通知をすべて配送する。"""
    bus = StudentChangeEventBus()
    student_id = StudentID("21D5109047B")
    received: list[StudentID] = []
    bus.subscribe(student_id, received.append)

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(bus.notify, [student_id] * 40))

    assert received == [student_id] * 40
