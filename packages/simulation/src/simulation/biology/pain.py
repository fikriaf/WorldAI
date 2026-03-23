from ..systems.base import System
from ..types import TickContext, WorldEvent, Agent
from dataclasses import dataclass
from typing import Dict


@dataclass
class PainResponse:
    acute_threshold: float = 0.3
    chronic_threshold: float = 0.6
    max_pain_level: float = 1.0


class PainSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self._pain_responses: Dict[str, list[float]] = {}
        self._analgesia_factors: Dict[str, float] = {}

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.cognitive_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        events = []

        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue

            pain_level = self._compute_pain_level(agent)

            if pain_level > 0.1:
                self._process_pain_response(agent, pain_level, events)

                self._record_pain_history(agent.id, pain_level)

                self._update_emotional_state(agent, pain_level)

        return events

    def _compute_pain_level(self, agent: Agent) -> float:
        damage_pain = 0.0
        if agent.health < 0.8:
            damage_pain = (0.8 - agent.health) * 1.25

        starvation_pain = 0.0
        if agent.energy < 0.2:
            starvation_pain = (0.2 - agent.energy) * 2.0

        inflammation_pain = agent.inflammation_level * 0.8

        isolation_pain = 0.0
        if agent.neural_complexity > 3:
            nearby = self._count_nearby_agents(agent)
            if nearby == 0:
                isolation_pain = 0.3
            elif nearby < 3:
                isolation_pain = 0.15

        physical_pain = damage_pain + starvation_pain + inflammation_pain

        total_pain = physical_pain + isolation_pain

        analgesia = self._get_analgesia(agent.id)
        total_pain *= 1.0 - analgesia

        return min(1.0, max(0.0, total_pain))

    def _count_nearby_agents(self, agent: Agent) -> int:
        count = 0
        for other in self.world.agents.values():
            if other.id == agent.id or not other.is_alive:
                continue
            dx = other.position.x - agent.position.x
            dy = other.position.y - agent.position.y
            if dx * dx + dy * dy < agent.sensory_range * agent.sensory_range:
                count += 1
        return count

    def _get_analgesia(self, agent_id: str) -> float:
        if agent_id not in self._analgesia_factors:
            self._analgesia_factors[agent_id] = 0.0
        return self._analgesia_factors[agent_id]

    def _process_pain_response(self, agent: Agent, pain_level: float, events: list):
        if pain_level > 0.7:
            agent.emotion.fear = min(1.0, agent.emotion.fear + pain_level * 0.3)
            agent.emotion.sadness = min(1.0, agent.emotion.sadness + pain_level * 0.2)

            target = self._find_nearest_safe_location(agent)
            if target:
                escape_dir_x = target[0] - agent.position.x
                escape_dir_y = target[1] - agent.position.y
                mag = (escape_dir_x**2 + escape_dir_y**2) ** 0.5
                if mag > 0:
                    agent.velocity.x += escape_dir_x / mag * pain_level * 0.5
                    agent.velocity.y += escape_dir_y / mag * pain_level * 0.5

        elif pain_level > 0.4:
            agent.emotion.fear = min(1.0, agent.emotion.fear + pain_level * 0.1)

        if pain_level > 0.5:
            agent.health = max(0, agent.health - pain_level * 0.02)
            agent.energy = max(0, agent.energy - pain_level * 0.01)

    def _find_nearest_safe_location(self, agent: Agent) -> tuple:
        best_location = None
        lowest_threat = float("inf")

        search_radius = agent.sensory_range * 2

        for (x, y), cell in self.world.grid.items():
            dx = x - agent.position.x
            dy = y - agent.position.y
            dist = (dx * dx + dy * dy) ** 0.5

            if dist > search_radius:
                continue

            threat = cell.temperature / 100
            threat += sum(cell.chemical_pool.values()) / 10

            if agent.group_id:
                group_members = sum(
                    1
                    for a in self.world.agents.values()
                    if a.group_id == agent.group_id and a.is_alive
                )
                if group_members > 0:
                    threat -= 0.1

            if threat < lowest_threat:
                lowest_threat = threat
                best_location = (float(x), float(y))

        return best_location

    def _record_pain_history(self, agent_id: str, pain_level: float):
        if agent_id not in self._pain_responses:
            self._pain_responses[agent_id] = []

        self._pain_responses[agent_id].append(pain_level)

        if len(self._pain_responses[agent_id]) > 100:
            self._pain_responses[agent_id] = self._pain_responses[agent_id][-100:]

    def _update_emotional_state(self, agent: Agent, pain_level: float):
        if pain_level > 0.5:
            agent.emotion.fear = min(1.0, agent.emotion.fear + 0.05)
            agent.emotion.sadness = min(1.0, agent.emotion.sadness + 0.05)
            agent.emotion.disgust = min(1.0, agent.emotion.disgust + 0.03)

        if pain_level < 0.2 and agent.health > 0.7:
            agent.emotion.joy = min(1.0, agent.emotion.joy + 0.02)

    def get_pain_stats(self) -> Dict:
        all_pain = []
        for pain_history in self._pain_responses.values():
            if pain_history:
                all_pain.extend(pain_history[-10:])

        if not all_pain:
            return {"avg_pain": 0.0, "high_pain_agents": 0, "chronic_pain_agents": 0}

        avg_pain = sum(all_pain) / len(all_pain)
        high_pain = sum(1 for p in all_pain if p > 0.6)

        chronic_count = 0
        for history in self._pain_responses.values():
            if len(history) >= 50:
                recent_avg = sum(history[-20:]) / 20
                if recent_avg > 0.3:
                    chronic_count += 1

        return {
            "avg_pain": avg_pain,
            "high_pain_agents": high_pain,
            "chronic_pain_agents": chronic_count,
        }
