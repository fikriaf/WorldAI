from ..systems.base import System
from ..types import TickContext, WorldEvent, EventType, ElementType
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class AutocatalyticSet:
    elements: List[ElementType]
    reaction_rate: float
    catalysts: List[ElementType]
    product: ElementType
    is_self_replicating: bool = False


class ProtoMetabolismSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self._autocatalytic_sets: List[AutocatalyticSet] = []
        self._reaction_complexes: Dict[tuple, float] = {}
        self._viable_chemistry_regions: List[tuple] = []
        self._init_autocatalytic_sets()

    def _init_autocatalytic_sets(self):
        self._autocatalytic_sets = [
            AutocatalyticSet(
                elements=[ElementType.PRIMUM, ElementType.AQUA],
                reaction_rate=0.1,
                catalysts=[ElementType.LAPIS],
                product=ElementType.TERRA,
            ),
            AutocatalyticSet(
                elements=[ElementType.TERRA, ElementType.AETHER],
                reaction_rate=0.15,
                catalysts=[ElementType.LAPIS, ElementType.IGNIS],
                product=ElementType.PRIMUM,
                is_self_replicating=True,
            ),
            AutocatalyticSet(
                elements=[ElementType.IGNIS, ElementType.AQUA],
                reaction_rate=0.08,
                catalysts=[ElementType.AETHER],
                product=ElementType.TERRA,
            ),
            AutocatalyticSet(
                elements=[ElementType.PRIMUM, ElementType.TERRA, ElementType.AQUA],
                reaction_rate=0.05,
                catalysts=[ElementType.LAPIS, ElementType.IGNIS],
                product=ElementType.IGNIS,
                is_self_replicating=True,
            ),
            AutocatalyticSet(
                elements=[ElementType.TERRA, ElementType.TERRA],
                reaction_rate=0.12,
                catalysts=[ElementType.AETHER],
                product=ElementType.AETHER,
                is_self_replicating=True,
            ),
        ]

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.chemistry_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        events = []

        self._identify_viable_regions()

        for (x, y), cell in self.world.grid.items():
            if (x, y) not in self._viable_chemistry_regions:
                continue

            autocatalytic_events = self._process_autocatalysis(cell, ctx)
            events.extend(autocatalytic_events)

        return events

    def _identify_viable_regions(self):
        self._viable_chemistry_regions = []

        for (x, y), cell in self.world.grid.items():
            if cell.temperature < 10 or cell.temperature > 80:
                continue

            energy_density = sum(cell.chemical_pool.values())
            if energy_density < 0.5:
                continue

            element_diversity = len([e for e in cell.chemical_pool.values() if e > 0.1])
            if element_diversity >= 3:
                self._viable_chemistry_regions.append((x, y))

    def _process_autocatalysis(self, cell, ctx: TickContext) -> list[WorldEvent]:
        events = []

        temperature_factor = self._get_temperature_factor(cell.temperature)

        for ac_set in self._autocatalytic_sets:
            if not self._can_react(cell, ac_set.elements):
                continue

            reaction_prob = ac_set.reaction_rate * temperature_factor

            catalyst_bonus = 0.0
            for cat in ac_set.catalysts:
                catalyst_bonus += cell.chemical_pool.get(cat, 0) * 0.1

            total_prob = min(1.0, reaction_prob + catalyst_bonus)

            if np.random.random() < total_prob:
                for reactant in ac_set.elements:
                    cell.chemical_pool[reactant] = max(0, cell.chemical_pool.get(reactant, 0) - 0.1)

                current_product = cell.chemical_pool.get(ac_set.product, 0)
                cell.chemical_pool[ac_set.product] = current_product + 0.15

                if ac_set.is_self_replicating:
                    events.append(
                        WorldEvent(
                            tick=ctx.tick,
                            type=EventType.CHEMICAL_REACTION,
                            data={
                                "type": "autocatalytic",
                                "location": (cell.x, cell.y),
                                "product": ac_set.product.value,
                                "self_replicating": True,
                            },
                        )
                    )

        return events

    def _can_react(self, cell, required_elements: List[ElementType]) -> bool:
        for elem in required_elements:
            if cell.chemical_pool.get(elem, 0) < 0.1:
                return False
        return True

    def _get_temperature_factor(self, temperature: float) -> float:
        if temperature < 20:
            return 0.2 + (temperature - 10) / 10 * 0.6
        elif temperature < 50:
            return 0.8 + (temperature - 20) / 30 * 0.2
        elif temperature < 70:
            return 1.0
        else:
            return max(0, 1.0 - (temperature - 70) / 20)

    def get_complexity_score(self) -> float:
        if not self._viable_chemistry_regions:
            return 0.0

        total_complexity = 0.0
        for x, y in self._viable_chemistry_regions:
            cell = self.world.grid.get((x, y))
            if cell:
                element_count = len([e for e in cell.chemical_pool.values() if e > 0.1])
                energy = sum(cell.chemical_pool.values())
                temp_norm = 1.0 - abs(cell.temperature - 45) / 45
                total_complexity += element_count * energy * temp_norm

        return (
            total_complexity / len(self._viable_chemistry_regions)
            if self._viable_chemistry_regions
            else 0.0
        )

    def count_autocatalytic_sites(self) -> int:
        return len(self._viable_chemistry_regions)
