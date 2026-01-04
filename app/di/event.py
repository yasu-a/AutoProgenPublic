from functools import cache

from shared.domain.interface.event import IEventBus
from shared.infra.event import QtEventBus


@cache
def get_event_bus() -> IEventBus:
    return QtEventBus()
