from ..systems.base import System
from ..types import TickContext, WorldEvent, EventType, Agent
from dataclasses import dataclass
from typing import Dict, List
import numpy as np


@dataclass
class PlaySession:
    agent_id: str
    duration: int = 0
    social_partners: List[str] = None
    energy_cost: float = 0.0

    def __post_init__(self):
        if self.social_partners is None:
            self.social_partners = []


class PlaySystem(System):
    def __init__(self, world):
        super().__init__(world)
        self._active_plays: Dict[str, PlaySession] = {}
        self._play_history: List[dict] = []
        self._skill_development: Dict[str, Dict[str, float]] = {}

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.biology_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        events = []

        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue

            if not self._should_play(agent):
                if agent.id in self._active_plays:
                    self._end_play_session(agent, events, ctx)
                continue

            if agent.id not in self._active_plays:
                self._start_play_session(agent)

            if agent.id in self._active_plays:
                self._process_play(agent, events, ctx)

        return events

    def _should_play(self, agent: Agent) -> bool:
        if agent.neural_complexity < 1:
            return False

        if agent.stage.value == "neonatal" and agent.age_ticks > 10:
            return True
        if agent.stage.value == "juvenile":
            return True
        if agent.stage.value == "adolescent" and agent.energy > 0.4:
            return True

        if agent.emotion.joy > 0.6 and agent.energy > 0.5:
            return True

        if agent.group_id and agent.energy > 0.4:
            nearby = self._count_group_members_nearby(agent)
            if nearby >= 1:
                return True

        return False

    def _count_group_members_nearby(self, agent: Agent) -> int:
        if not agent.group_id:
            return 0

        count = 0
        for other in self.world.agents.values():
            if other.id == agent.id or not other.is_alive:
                continue
            if other.group_id != agent.group_id:
                continue

            dx = other.position.x - agent.position.x
            dy = other.position.y - agent.position.y
            if dx * dx + dy * dy < (agent.sensory_range * 1.5) ** 2:
                count += 1

        return count

    def _start_play_session(self, agent: Agent):
        partners = []

        if agent.group_id:
            for other in self.world.agents.values():
                if other.id == agent.id or not other.is_alive:
                    continue
                if other.group_id != agent.group_id:
                    continue

                dx = other.position.x - agent.position.x
                dy = other.position.y - agent.position.y
                if dx * dx + dy * dy < (agent.sensory_range * 1.5) ** 2:
                    partners.append(other.id)

        self._active_plays[agent.id] = PlaySession(agent_id=agent.id, social_partners=partners)

        if agent.id not in self._skill_development:
            self._skill_development[agent.id] = {
                "motor": 0.0,
                "social": 0.0,
                "exploration": 0.0,
                "creativity": 0.0,
            }

    def _process_play(self, agent: Agent, events: list, ctx: TickContext):
        play_session = self._active_plays[agent.id]

        play_session.duration += 1

        energy_cost = 0.02 * (1 + len(play_session.social_partners) * 0.5)
        agent.energy = max(0, agent.energy - energy_cost)
        play_session.energy_cost += energy_cost

        agent.emotion.joy = min(1.0, agent.emotion.joy + 0.05)

        if play_session.duration > 5:
            self._develop_skills(agent, play_session)

        if agent.energy < 0.2 or play_session.duration > 30:
            self._end_play_session(agent, events, ctx)

    def _develop_skills(self, agent: Agent, play_session: PlaySession):
        skills = self._skill_development.get(agent.id, {})

        if play_session.social_partners:
            skills["social"] = skills.get("social", 0) + 0.03
            for partner in play_session.social_partners:
                if partner in self.world.agents:
                    partner_brain = self._get_brain(partner)
                    if partner_brain:
                        agent.reputation[partner] = min(
                            1.0, agent.reputation.get(partner, 0.5) + 0.02
                        )

        exploration_chance = np.random.random()
        if exploration_chance < 0.3:
            skills["exploration"] = skills.get("exploration", 0) + 0.02

        if play_session.duration > 10:
            skills["creativity"] = skills.get("creativity", 0) + 0.02

        skills["motor"] = skills.get("motor", 0) + 0.01

        for skill in skills:
            skills[skill] = min(1.0, skills[skill])

        self._skill_development[agent.id] = skills

    def _get_brain(self, agent_id: str):
        return None

    def _end_play_session(self, agent: Agent, events: list, ctx: TickContext):
        if agent.id not in self._active_plays:
            return

        session = self._active_plays[agent.id]

        self._play_history.append(
            {
                "tick": ctx.tick,
                "agent_id": agent.id,
                "duration": session.duration,
                "partners": session.social_partners.copy(),
                "skills": self._skill_development.get(agent.id, {}).copy(),
            }
        )

        if len(self._play_history) > 100:
            self._play_history = self._play_history[-100:]

        del self._active_plays[agent.id]

        events.append(
            WorldEvent(
                tick=ctx.tick,
                type=EventType.GOD_MODE_INTERVENTION,
                data={
                    "play_completed": agent.id,
                    "duration": session.duration,
                    "skills_gained": self._skill_development.get(agent.id, {}),
                },
            )
        )

    def get_play_stats(self) -> Dict:
        active_plays = len(self._active_plays)

        if not self._play_history:
            return {"active_sessions": active_plays, "total_play_events": 0, "avg_duration": 0}

        durations = [p["duration"] for p in self._play_history[-20:]]

        return {
            "active_sessions": active_plays,
            "total_play_events": len(self._play_history),
            "avg_duration": sum(durations) / len(durations) if durations else 0,
            "avg_partners": np.mean([len(p["partners"]) for p in self._play_history[-20:]])
            if self._play_history
            else 0,
        }

    def get_skill_levels(self, agent_id: str) -> Dict[str, float]:
        return self._skill_development.get(
            agent_id, {"motor": 0.0, "social": 0.0, "exploration": 0.0, "creativity": 0.0}
        )
