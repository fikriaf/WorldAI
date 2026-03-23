from collections import defaultdict
from ..systems.base import System
from ..types import TickContext, WorldEvent, ElementType


class CarbonCycle(System):
    def __init__(self, world):
        super().__init__(world)
        self._initial_carbon = None
        self._carbon_history = []

    def _compute_carbon_totals(self) -> tuple[float, float, float]:
        carbon_in_cells = sum(
            cell.chemical_pool.get(ElementType.TERRA, 0) for cell in self.world.grid.values()
        )
        carbon_in_agents = sum(
            agent.mass * 0.5 for agent in self.world.agents.values() if agent.is_alive
        )
        return carbon_in_cells, carbon_in_agents, carbon_in_cells + carbon_in_agents

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        if not ctx.biology_tick:
            return []

        carbon_in_cells, carbon_in_agents, carbon_total = self._compute_carbon_totals()

        if self._initial_carbon is None:
            self._initial_carbon = carbon_total

        self._carbon_history.append(carbon_total)
        if len(self._carbon_history) > 1000:
            self._carbon_history.pop(0)

        for agent in self.world.agents.values():
            if not agent.is_alive:
                cell_x = int(agent.position.x) % self.world.config.grid_width
                cell_y = int(agent.position.y) % self.world.config.grid_height
                cell = self.world.grid.get((cell_x, cell_y))
                if cell:
                    cell.chemical_pool[ElementType.TERRA] += agent.mass * 0.3

        for agent in self.world.agents.values():
            if agent.is_alive:
                cell_x = int(agent.position.x) % self.world.config.grid_width
                cell_y = int(agent.position.y) % self.world.config.grid_height
                cell = self.world.grid.get((cell_x, cell_y))
                if cell and agent.energy < 0.5:
                    respiration_rate = agent.mass * 0.001
                    cell.chemical_pool[ElementType.TERRA] += respiration_rate
                    cell.chemical_pool[ElementType.AQUA] += respiration_rate * 0.5

        return []

    def get_carbon_balance(self) -> dict:
        if self._initial_carbon is None or not self._carbon_history:
            return {
                "initial_carbon": 0.0,
                "current_carbon": 0.0,
                "balance_ratio": 1.0,
                "leakage_rate": 0.0,
                "closure_percentage": 100.0,
            }
        current = self._carbon_history[-1]
        avg_history = sum(self._carbon_history) / len(self._carbon_history)
        initial = self._initial_carbon
        balance_ratio = current / initial if initial > 0 else 1.0
        leakage_rate = abs(current - initial) / initial if initial > 0 else 0.0
        closure_percentage = max(0.0, min(100.0, (1.0 - leakage_rate) * 100))
        return {
            "initial_carbon": initial,
            "current_carbon": current,
            "balance_ratio": balance_ratio,
            "leakage_rate": leakage_rate,
            "closure_percentage": closure_percentage,
            "avg_carbon": avg_history,
        }


class NitrogenCycle(System):
    def __init__(self, world):
        super().__init__(world)
        self._initial_ignis = None
        self._ignis_history = []

    def _compute_ignis_totals(self) -> tuple[float, float, float]:
        ignis_in_cells = sum(
            cell.chemical_pool.get(ElementType.IGNIS, 0) for cell in self.world.grid.values()
        )
        ignis_in_agents = sum(
            agent.mass * 0.02 for agent in self.world.agents.values() if agent.is_alive
        )
        return ignis_in_cells, ignis_in_agents, ignis_in_cells + ignis_in_agents

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        if not ctx.biology_tick:
            return []

        ignis_cells, ignis_agents, ignis_total = self._compute_ignis_totals()

        if self._initial_ignis is None:
            self._initial_ignis = ignis_total

        self._ignis_history.append(ignis_total)
        if len(self._ignis_history) > 1000:
            self._ignis_history.pop(0)

        for cell in self.world.grid.values():
            ignis = cell.chemical_pool.get(ElementType.IGNIS, 0)

            fixation_chance = 0.001
            if ignis > 0.5:
                if self.world.prng.random_global() < fixation_chance:
                    cell.chemical_pool[ElementType.IGNIS] -= 0.1
                    cell.chemical_pool[ElementType.TERRA] += 0.05
                    cell.chemical_pool[ElementType.AETHER] += 0.02

            if ignis > 1.0:
                denitrification_rate = min(0.05, ignis * 0.01)
                cell.chemical_pool[ElementType.IGNIS] -= denitrification_rate

        for agent in self.world.agents.values():
            if not agent.is_alive:
                cell_x = int(agent.position.x) % self.world.config.grid_width
                cell_y = int(agent.position.y) % self.world.config.grid_height
                cell = self.world.grid.get((cell_x, cell_y))
                if cell:
                    cell.chemical_pool[ElementType.IGNIS] += agent.mass * 0.02

        return []

    def get_nitrogen_balance(self) -> dict:
        if self._initial_ignis is None or not self._ignis_history:
            return {
                "initial_ignis": 0.0,
                "current_ignis": 0.0,
                "balance_ratio": 1.0,
                "closure_percentage": 100.0,
            }
        current = self._ignis_history[-1]
        initial = self._initial_ignis
        balance_ratio = current / initial if initial > 0 else 1.0
        leakage_rate = abs(current - initial) / initial if initial > 0 else 0.0
        closure_percentage = max(0.0, min(100.0, (1.0 - leakage_rate) * 100))
        return {
            "initial_ignis": initial,
            "current_ignis": current,
            "balance_ratio": balance_ratio,
            "closure_percentage": closure_percentage,
        }


class WaterCycle(System):
    def __init__(self, world):
        super().__init__(world)
        self._initial_aqua = None
        self._aqua_history = []
        self._evaporation_rate = 0.01
        self._precipitation_threshold = 0.8

    def _compute_aqua_totals(self) -> tuple[float, float, float]:
        aqua_in_cells = sum(
            cell.chemical_pool.get(ElementType.AQUA, 0) for cell in self.world.grid.values()
        )
        aqua_in_agents = sum(
            agent.mass * 0.1 for agent in self.world.agents.values() if agent.is_alive
        )
        return aqua_in_cells, aqua_in_agents, aqua_in_cells + aqua_in_agents

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        if not ctx.biology_tick or ctx.tick % 10 != 0:
            return []

        aqua_cells, aqua_agents, aqua_total = self._compute_aqua_totals()

        if self._initial_aqua is None:
            self._initial_aqua = aqua_total

        self._aqua_history.append(aqua_total)
        if len(self._aqua_history) > 1000:
            self._aqua_history.pop(0)

        aqua_by_row = defaultdict(float)
        for (x, y), cell in self.world.grid.items():
            aqua = cell.chemical_pool.get(ElementType.AQUA, 0)
            aqua_by_row[y] += aqua

        for (x, y), cell in self.world.grid.items():
            row_avg = aqua_by_row[y] / self.world.config.grid_width

            diff = row_avg - cell.chemical_pool.get(ElementType.AQUA, 0)

            if abs(diff) > 0.1:
                flow = diff * 0.05
                cell.chemical_pool[ElementType.AQUA] = max(
                    0, cell.chemical_pool.get(ElementType.AQUA, 0) + flow
                )

        for agent in self.world.agents.values():
            if not agent.is_alive:
                cell_x = int(agent.position.x) % self.world.config.grid_width
                cell_y = int(agent.position.y) % self.world.config.grid_height
                cell = self.world.grid.get((cell_x, cell_y))
                if cell:
                    cell.chemical_pool[ElementType.AQUA] += agent.mass * 0.1

        return []

    def get_water_balance(self) -> dict:
        if self._initial_aqua is None or not self._aqua_history:
            return {
                "initial_aqua": 0.0,
                "current_aqua": 0.0,
                "balance_ratio": 1.0,
                "closure_percentage": 100.0,
            }
        current = self._aqua_history[-1]
        initial = self._initial_aqua
        balance_ratio = current / initial if initial > 0 else 1.0
        leakage_rate = abs(current - initial) / initial if initial > 0 else 0.0
        closure_percentage = max(0.0, min(100.0, (1.0 - leakage_rate) * 100))
        return {
            "initial_aqua": initial,
            "current_aqua": current,
            "balance_ratio": balance_ratio,
            "closure_percentage": closure_percentage,
        }


class BiogeochemicalCycleSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self.carbon = CarbonCycle(world)
        self.nitrogen = NitrogenCycle(world)
        self.water = WaterCycle(world)

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        events = []

        events.extend(self.carbon.update(ctx))
        events.extend(self.nitrogen.update(ctx))
        events.extend(self.water.update(ctx))

        return events

    def get_cycle_closure_stats(self) -> dict:
        carbon_stats = self.carbon.get_carbon_balance()
        nitrogen_stats = self.nitrogen.get_nitrogen_balance()
        water_stats = self.water.get_water_balance()

        avg_closure = (
            carbon_stats["closure_percentage"]
            + nitrogen_stats["closure_percentage"]
            + water_stats["closure_percentage"]
        ) / 3.0

        return {
            "carbon": carbon_stats,
            "nitrogen": nitrogen_stats,
            "water": water_stats,
            "average_closure_percentage": avg_closure,
            "all_cycles_balanced": avg_closure > 95.0,
        }
