from ..systems.base import System
from ..types import TickContext, WorldEvent, EventType, Agent
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CorruptionState:
    agent_id: str
    bribe_tendency: float = 0.0
    corruption_exposure: float = 0.0
    norm_violation_count: int = 0
    regulatory_capture_level: float = 0.0
    last_bribe_tick: int = -1000


class CorruptionSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self._corruption_states: Dict[str, CorruptionState] = {}
        self._norm_erosion_rate = 0.001
        self._bribe_cooldown = 50

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.social_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        events = []

        if not hasattr(self.world, "politics"):
            return events

        for agent in self.world.agents.values():
            if not agent.is_alive or agent.neural_complexity < 2:
                continue

            state = self._get_or_create_state(agent)
            self._update_corruption_state(agent, state, ctx)
            self._check_principal_agent_corruption(agent, state, ctx, events)
            self._check_regulatory_capture(agent, state, ctx, events)
            self._apply_corruption_effects(agent, state)

        return events

    def _get_or_create_state(self, agent: Agent) -> CorruptionState:
        if agent.id not in self._corruption_states:
            self._corruption_states[agent.id] = CorruptionState(agent_id=agent.id)
        return self._corruption_states[agent.id]

    def _update_corruption_state(self, agent: Agent, state: CorruptionState, ctx: TickContext):
        if agent.group_id:
            group_members = [
                a for a in self.world.agents.values() if a.group_id == agent.group_id and a.is_alive
            ]
            if len(group_members) > 0:
                avg_neural = np.mean([a.neural_complexity for a in group_members])
                if agent.neural_complexity > avg_neural + 1:
                    state.bribe_tendency = min(1.0, state.bribe_tendency + 0.01)

        state.corruption_exposure = max(0.0, state.corruption_exposure - self._norm_erosion_rate)

        if agent.emotion.anger > 0.6 or agent.emotion.disgust > 0.6:
            state.corruption_exposure = min(1.0, state.corruption_exposure + 0.02)

    def _check_principal_agent_corruption(
        self, agent: Agent, state: CorruptionState, ctx: TickContext, events: List[WorldEvent]
    ):
        if not hasattr(self.world.politics, "political_entities"):
            return

        if ctx.tick - state.last_bribe_tick < self._bribe_cooldown:
            return

        if agent.neural_complexity < 3:
            return

        for entity_id, entity in self.world.politics.political_entities.items():
            if entity.power > 0.5 and state.bribe_tendency > 0.3:
                if np.random.random() < state.bribe_tendency * 0.001:
                    state.last_bribe_tick = ctx.tick
                    state.norm_violation_count += 1

                    if entity.power > 0.7:
                        state.corruption_exposure = min(1.0, state.corruption_exposure + 0.05)

                    events.append(
                        WorldEvent(
                            tick=ctx.tick,
                            type=EventType.GOD_MODE_INTERVENTION,
                            data={"corruption_type": "bribe", "entity_id": entity_id},
                            source_id=agent.id,
                        )
                    )

    def _check_regulatory_capture(
        self, agent: Agent, state: CorruptionState, ctx: TickContext, events: List[WorldEvent]
    ):
        if not hasattr(self.world.politics, "political_entities"):
            return

        if agent.group_id:
            group_members = [
                a for a in self.world.agents.values() if a.group_id == agent.group_id and a.is_alive
            ]

            wealth = agent.economy_wealth if hasattr(agent, "economy_wealth") else 0.5
            if wealth > 0.7:
                for entity_id, entity in self.world.politics.political_entities.items():
                    if entity.power > 0.3 and entity.power < 0.8:
                        if np.random.random() < 0.001:
                            state.regulatory_capture_level = min(
                                1.0, state.regulatory_capture_level + 0.1
                            )
                            entity.power = min(1.0, entity.power + 0.02)

    def _apply_corruption_effects(self, agent: Agent, state: CorruptionState):
        agent.emotion.disgust = min(1.0, agent.emotion.disgust + state.corruption_exposure * 0.05)

        if state.norm_violation_count > 5:
            agent.emotion.trust = max(0.0, agent.emotion.trust - 0.02)
            agent.emotion.anger = min(1.0, agent.emotion.anger + 0.01)

        if state.regulatory_capture_level > 0.5:
            if hasattr(self.world, "economy"):
                agent.emotion.anger = min(1.0, agent.emotion.anger + 0.02)

    def get_corruption_stats(self) -> Dict:
        if not self._corruption_states:
            return {"total_tracked": 0}

        avg_exposure = np.mean([s.corruption_exposure for s in self._corruption_states.values()])
        avg_bribe = np.mean([s.bribe_tendency for s in self._corruption_states.values()])

        return {
            "total_tracked": len(self._corruption_states),
            "avg_corruption_exposure": avg_exposure,
            "avg_bribe_tendency": avg_bribe,
            "total_norm_violations": sum(
                s.norm_violation_count for s in self._corruption_states.values()
            ),
        }
