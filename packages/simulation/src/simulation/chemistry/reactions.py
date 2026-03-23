import numpy as np
from numba import njit
from ..systems.base import System
from ..types import TickContext, WorldEvent, EventType, ElementType


REACTION_RULES = [
    (["P", "A"], ["T"], 1.0, -5.0),
    (["T", "A"], ["I"], 0.8, -3.0),
    (["I", "Ae"], ["P"], 0.5, -2.0),
    (["T", "T"], ["T", "T"], 0.3, -1.0),
    (["P", "I"], ["Ae"], 0.6, -4.0),
    (["A", "T"], ["L"], 0.4, -1.5),
    (["I", "A"], ["I"], 0.7, -0.5),
    (["P", "P"], ["P"], 0.5, -1.0),
    (["Ae", "T"], ["L"], 0.3, -2.5),
    (["L", "P"], ["Ae"], 0.4, -1.0),
    (["P", "T", "A"], ["T", "I"], 0.2, -6.0),
    (["I", "I"], ["Ae"], 0.4, -3.5),
    (["P", "L"], ["Ae", "P"], 0.3, -2.0),
    (["T", "I", "Ae"], ["P", "I"], 0.25, -4.5),
    (["A", "I"], ["T", "Ae"], 0.35, -3.0),
    (["L", "Ae"], ["T", "L"], 0.2, -1.8),
]


@njit
def arrhenius_rate(T: float, Ea: float, preexp: float = 1.0) -> float:
    k_B = 8.617e-5
    return preexp * np.exp(-Ea / (k_B * max(T, 1.0)))


class ChemistrySystem(System):
    def update(self, ctx: TickContext) -> list[WorldEvent]:
        if not ctx.chemistry_tick:
            return []

        events = []
        for (x, y), cell in self.world.grid.items():
            cell_events = self._process_cell_reactions(cell, ctx)
            events.extend(cell_events)

        return events

    def _process_cell_reactions(self, cell, ctx) -> list[WorldEvent]:
        events = []
        temp = max(cell.temperature, 1.0)

        for reactants, products, preexp, delta_G in REACTION_RULES:
            if not self._reactants_available(cell, reactants):
                continue

            rate = arrhenius_rate(temp, abs(delta_G), preexp)
            if np.random.random() < rate * 0.1:
                self._consume_reactants(cell, reactants)
                self._add_products(cell, products)

                events.append(
                    WorldEvent(
                        tick=ctx.tick,
                        type=EventType.CHEMICAL_REACTION,
                        data={
                            "cell_x": cell.x,
                            "cell_y": cell.y,
                            "reactants": str(reactants),
                            "products": str(products),
                            "delta_G": delta_G,
                        },
                    )
                )

        return events

    def _reactants_available(self, cell, reactants) -> bool:
        for r in reactants:
            elem = ElementType(r)
            if cell.chemical_pool.get(elem, 0) < 0.5:
                return False
        return True

    def _consume_reactants(self, cell, reactants):
        for r in reactants:
            elem = ElementType(r)
            cell.chemical_pool[elem] = cell.chemical_pool.get(elem, 0) - 0.5

    def _add_products(self, cell, products):
        for p in products:
            elem = ElementType(p)
            cell.chemical_pool[elem] = cell.chemical_pool.get(elem, 0) + 0.3
