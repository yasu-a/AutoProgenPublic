from abc import abstractmethod
from typing import Callable, Type, TypeVar

from shared.domain.value.event import DomainEvent

T = TypeVar("T", bound=DomainEvent)


# QObjectと干渉するためABCは省略
# noinspection PyAbstractClass
class IEventBus:
    @abstractmethod
    def publish(self, event: DomainEvent) -> None:
        """イベントを発行する"""
        raise NotImplementedError()

    @abstractmethod
    def subscribe(self, event_type: Type[T], callback: Callable[[T], None]) -> None:
        """特定の種類のイベントを購読する"""
        raise NotImplementedError()

    @abstractmethod
    def unsubscribe(self, event_type: Type[DomainEvent], callback: Callable) -> None:
        raise NotImplementedError()
