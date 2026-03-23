from ..systems.base import System
from ..types import TickContext, WorldEvent, EventType, Agent
import random


class ImmuneSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self._pathogen_types = ["viral", "bacterial", "parasitic", "prion"]

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.biology_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        events = []

        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue

            self._process_pathogen_exposure(agent)
            self._process_innate_immunity(agent)
            self._process_inflammation(agent)

        return events

    def _process_pathogen_exposure(self, agent: Agent):
        cell_x = int(agent.position.x) % self.world.config.grid_width
        cell_y = int(agent.position.y) % self.world.config.grid_height
        cell = self.world.grid.get((cell_x, cell_y))

        if cell and sum(cell.chemical_pool.values()) > 1.0:
            pathogen_type = random.choice(self._pathogen_types)
            agent.pathogen_exposure += 0.1

            if pathogen_type not in agent.immune_memory:
                if agent.pathogen_exposure > 0.3:
                    agent.immune_memory.append(pathogen_type)

    def _process_innate_immunity(self, agent: Agent):
        if agent.pathogen_exposure > 0:
            if agent.immune_system_strength > 0.5:
                agent.pathogen_exposure -= 0.05 * agent.immune_system_strength
            else:
                agent.pathogen_exposure -= 0.02

            if agent.pathogen_exposure < 0:
                agent.pathogen_exposure = 0

    def _process_inflammation(self, agent: Agent):
        agent.inflammation_level += agent.pathogen_exposure * 0.5

        if agent.inflammation_level > 0.3:
            agent.health -= agent.inflammation_level * 0.1
            agent.energy -= agent.inflammation_level * 0.05

        agent.inflammation_level *= 0.9

        if agent.inflammation_level < 0:
            agent.inflammation_level = 0

    def trigger_immune_response(self, agent: Agent, pathogen_type: str):
        if pathogen_type in agent.immune_memory:
            agent.inflammation_level += 0.3
            agent.immune_system_strength = min(1.0, agent.immune_system_strength + 0.1)
        else:
            agent.inflammation_level += 0.8

    def get_immune_stats(self) -> dict:
        total_agents = 0
        avg_immunity = 0.0
        avg_inflammation = 0.0

        for agent in self.world.agents.values():
            if agent.is_alive:
                total_agents += 1
                avg_immunity += agent.immune_system_strength
                avg_inflammation += agent.inflammation_level

        if total_agents > 0:
            avg_immunity /= total_agents
            avg_inflammation /= total_agents

        return {
            "total_agents": total_agents,
            "avg_immunity": avg_immunity,
            "avg_inflammation": avg_inflammation,
            "pathogen_types": self._pathogen_types,
        }
