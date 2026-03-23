from ..systems.base import System
from ..types import TickContext, WorldEvent


class DiffusionSystem(System):
    def update(self, ctx: TickContext) -> list[WorldEvent]:
        return []
