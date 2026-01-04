from collections import defaultdict
from typing import Callable, Type

from PyQt5.QtCore import QObject, pyqtSignal

from shared.domain.interface.event import IEventBus
from shared.domain.value.event import DomainEvent


class QtEventBus(QObject, IEventBus):
    """
    Qtシグナルを使用したイベントバス。
    スレッドセーフにイベントをメインスレッドへ配送します。
    """
    # 任意のPythonオブジェクト(イベント)を運ぶシグナル
    _signal = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        # イベント型ごとのコールバックリスト
        self._subscribers: dict[Type[DomainEvent], list[Callable]] = defaultdict(list)

        # 自分自身のシグナルを自分自身のスロットに接続
        # これにより、別スレッドから emit されても、_on_event_received はメインスレッドで実行される
        # noinspection PyUnresolvedReferences
        self._signal.connect(self._on_event_received)

    def publish(self, event: DomainEvent) -> None:
        """[Publisher側] イベントをバスに投げる"""
        # シグナル発火（スレッドセーフ）
        # noinspection PyUnresolvedReferences
        self._signal.emit(event)

    def subscribe(self, event_type: Type[DomainEvent], callback: Callable) -> None:
        """[Subscriber側] 欲しいイベントを登録する"""
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: Type[DomainEvent], callback: Callable) -> None:
        if event_type in self._subscribers:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)

    def _on_event_received(self, event: DomainEvent) -> None:
        """[内部処理] シグナル経由で受け取ったイベントを適切なコールバックに配る"""
        event_type = type(event)

        # 登録されているコールバックを順次実行
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(event)
                except Exception as e:
                    print(f"Error in event handler: {e}")
