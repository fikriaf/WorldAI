from ..systems.base import System
from ..types import TickContext, WorldEvent, EventType, ElementType


class ResourceCompetitionSystem(System):
    def __init__(self, world):
        super().__init__(world)

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        if not ctx.biology_tick:
            return []

        events = []

        for (x, y), cell in self.world.grid.items():
            agents_in_cell = [
                a
                for a in self.world.agents.values()
                if a.is_alive
                and int(a.position.x) % self.world.config.grid_width == x
                and int(a.position.y) % self.world.config.grid_height == y
            ]

            if len(agents_in_cell) <= 1:
                continue

            total_needed = sum(a.mass * 0.1 for a in agents_in_cell)

            resource_types = [ElementType.PRIMUM, ElementType.AQUA, ElementType.TERRA]

            for elem_type in resource_types:
                available = cell.chemical_pool.get(elem_type, 0)

                if available <= 0:
                    continue

                if len(agents_in_cell) == 1:
                    agent = agents_in_cell[0]
                    consumed = min(available, agent.mass * 0.1)
                    cell.chemical_pool[elem_type] -= consumed
                    agent.energy = min(1.0, agent.energy + consumed * 0.1)
                    continue

                allocations = self._allocate_resources(agents_in_cell, available)

                for agent, amount in allocations.items():
                    if amount > 0:
                        cell.chemical_pool[elem_type] -= amount
                        energy_gain = amount * 0.1
                        agent.energy = min(1.0, agent.energy + energy_gain)

        return events

    def _allocate_resources(self, agents: list, available: float) -> dict:
        if not agents:
            return {}

        if len(agents) == 1:
            return {agents[0]: available}

        energies = [a.energy for a in agents]
        masses = [a.mass for a in agents]

        total_energy = sum(energies)
        if total_energy > 0:
            energy_weights = [e / total_energy for e in energies]
        else:
            energy_weights = [1.0 / len(agents)] * len(agents)

        total_mass = sum(masses)
        if total_mass > 0:
            mass_weights = [m / total_mass for m in masses]
        else:
            mass_weights = [1.0 / len(agents)] * len(agents)

        combined_weights = [(e * 0.6 + m * 0.4) for e, m in zip(energy_weights, mass_weights)]

        total_weight = sum(combined_weights)
        if total_weight > 0:
            normalized_weights = [w / total_weight for w in combined_weights]
        else:
            normalized_weights = [1.0 / len(agents)] * len(agents)

        allocations = {}
        for agent, weight in zip(agents, normalized_weights):
            allocations[agent] = available * weight

        return allocations


class TerritorialSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self.territories: dict[tuple[int, int], str] = {}

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        if not ctx.biology_tick or ctx.tick % 10 != 0:
            return []

        events = []

        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue

            x = int(agent.position.x) % self.world.config.grid_width
            y = int(agent.position.y) % self.world.config.grid_height
            territory = (x, y)

            current_owner = self.territories.get(territory)

            if current_owner is None or current_owner == agent.id:
                self.territories[territory] = agent.id

            elif current_owner != agent.id:
                owner_agent = self.world.agents.get(current_owner)
                if owner_agent and owner_agent.is_alive:
                    strength_agent = self._compute_strength(agent)
                    strength_owner = self._compute_strength(owner_agent)

                    if strength_agent > strength_owner * 1.2:
                        self.territories[territory] = agent.id

        return events

    def _compute_strength(self, agent) -> float:
        strength = 0.0
        strength += agent.energy * 2.0
        strength += agent.health * 1.5
        strength += len(agent.genome.genes) * 0.1
        strength += agent.mass * 0.5
        return strength
