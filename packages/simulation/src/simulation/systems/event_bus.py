from typing import Callable
from collections import defaultdict
from ..types import WorldEvent, EventType


class EventBus:
    def __init__(self):
        self._subscribers: dict[EventType, list[Callable]] = defaultdict(list)
        self._events: list[WorldEvent] = []

    def subscribe(self, event_type: EventType, callback: Callable):
        self._subscribers[event_type].append(callback)

    def publish(self, event: WorldEvent):
        self._events.append(event)
        for callback in self._subscribers[event.type]:
            callback(event)

    def publish_batch(self, events: list[WorldEvent]):
        for event in events:
            self.publish(event)
