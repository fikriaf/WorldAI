from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .types import TickContext, WorldEvent


class System(ABC):
    def __init__(self, world):
        self.world = world

    def should_run(self, ctx: "TickContext") -> bool:
        return True

    @abstractmethod
    def update(self, ctx: "TickContext") -> list["WorldEvent"]:
        pass
