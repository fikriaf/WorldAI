from ..systems.base import System
from ..types import TickContext, WorldEvent, EventType, Agent
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class FirstContactState:
    agent_id: str
    disease_amplifier: float = 0.0
    cultural_shock: float = 0.0
    syncretic_blends: List[str] = field(default_factory=list)
    technology_absorbed: float = 0.0
    contact_history: List[int] = field(default_factory=list)


class FirstContactSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self._contact_states: Dict[str, FirstContactState] = {}
        self._disease_amplifier_base = 3.0
        self._shock_threshold = 0.7

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.social_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        events = []

        self._detect_contacts(ctx, events)

        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue

            state = self._get_or_create_state(agent)
            self._disease_amplification(agent, state, ctx, events)
            self._cultural_shock(agent, state, ctx)
            self._syncretism(agent, state, ctx, events)
            self._technology_transfer(agent, state, ctx)

        return events

    def _get_or_create_state(self, agent: Agent) -> FirstContactState:
        if agent.id not in self._contact_states:
            self._contact_states[agent.id] = FirstContactState(agent_id=agent.id)
        return self._contact_states[agent.id]

    def _detect_contacts(self, ctx: TickContext, events: List[WorldEvent]):
        contacted_pairs = set()

        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue

            for other in self.world.agents.values():
                if other.id == agent.id or not other.is_alive:
                    continue

                if agent.group_id is not None and other.group_id is not None:
                    if agent.group_id != other.group_id:
                        pair = tuple(sorted([agent.id, other.id]))
                        if pair not in contacted_pairs:
                            contacted_pairs.add(pair)

                            agent_state = self._get_or_create_state(agent)
                            other_state = self._get_or_create_state(other)

                            if ctx.tick not in agent_state.contact_history:
                                agent_state.contact_history.append(ctx.tick)
                            if ctx.tick not in other_state.contact_history:
                                other_state.contact_history.append(ctx.tick)

                            events.append(
                                WorldEvent(
                                    tick=ctx.tick,
                                    type=EventType.GOD_MODE_INTERVENTION,
                                    data={"first_contact": True},
                                    source_id=agent.id,
                                    target_id=other.id,
                                )
                            )

    def _disease_amplification(
        self, agent: Agent, state: FirstContactState, ctx: TickContext, events: List[WorldEvent]
    ):
        if len(state.contact_history) < 2:
            return

        time_since_contact = ctx.tick - state.contact_history[-1]

        if time_since_contact < 10:
            susceptibility = 1.0 - agent.health

            if hasattr(self.world, "immune"):
                immune_state = self.world.immune._immune_states.get(agent.id)
                if immune_state:
                    susceptibility *= 1.0 + immune_state.immune_complexity * 0.1

            state.disease_amplifier = min(
                2.0, state.disease_amplifier + susceptibility * self._disease_amplifier_base * 0.1
            )

            if state.disease_amplifier > 1.0 and np.random.random() < 0.05:
                agent.health = max(0, agent.health - state.disease_amplifier * 0.1)
                agent.inflammation_level = min(1.0, agent.inflammation_level + 0.1)

                events.append(
                    WorldEvent(
                        tick=ctx.tick,
                        type=EventType.GOD_MODE_INTERVENTION,
                        data={"contact_disease": True, "amplifier": state.disease_amplifier},
                        source_id=agent.id,
                    )
                )

    def _cultural_shock(self, agent: Agent, state: FirstContactState, ctx: TickContext):
        if len(state.contact_history) < 1:
            return

        cultural_familiarity = 0.0
        if agent.group_id:
            group_exposure = len(state.contact_history) / max(1, ctx.tick)
            cultural_familiarity = group_exposure

        state.cultural_shock = max(0, 1.0 - cultural_familiarity)

        if agent.neural_complexity > 2:
            shock_adapt_rate = (1.0 - agent.emotion.trust) * 0.1
            state.cultural_shock = max(0, state.cultural_shock - shock_adapt_rate)

        if state.cultural_shock > self._shock_threshold:
            agent.emotion.fear = min(1.0, agent.emotion.fear + 0.1)
            agent.emotion.trust = max(0.0, agent.emotion.trust - 0.05)

    def _syncretism(
        self, agent: Agent, state: FirstContactState, ctx: TickContext, events: List[WorldEvent]
    ):
        if agent.neural_complexity < 2 or not agent.group_id:
            return

        if len(state.contact_history) < 3:
            return

        adaptation_rate = agent.neural_complexity * 0.01

        if agent.emotion.trust > 0.5 and agent.emotion.anticipation > 0.3:
            if np.random.random() < adaptation_rate:
                blend_types = ["religious", "artistic", "technological", "political"]
                new_blend = np.random.choice(blend_types)

                if new_blend not in state.syncretic_blends:
                    state.syncretic_blends.append(new_blend)

                    events.append(
                        WorldEvent(
                            tick=ctx.tick,
                            type=EventType.GOD_MODE_INTERVENTION,
                            data={"syncretism": new_blend},
                            source_id=agent.id,
                        )
                    )

    def _technology_transfer(self, agent: Agent, state: FirstContactState, ctx: TickContext):
        if len(state.contact_history) < 2:
            return

        learning_capacity = agent.neural_complexity * 0.05

        if agent.group_id:
            group_tech = 0.0
            for other in self.world.agents.values():
                if other.group_id == agent.group_id and other.id != agent.id:
                    other_state = self._get_or_create_state(other)
                    group_tech = max(group_tech, other_state.technology_absorbed)

            learning_capacity += group_tech * 0.1

        if np.random.random() < learning_capacity:
            state.technology_absorbed = min(1.0, state.technology_absorbed + 0.05)

        if state.technology_absorbed > 0.5 and hasattr(self.world, "tool_use"):
            agent.tool_proficiency = min(1.0, getattr(agent, "tool_proficiency", 0) + 0.02)

    def get_first_contact_stats(self) -> Dict:
        if not self._contact_states:
            return {"total_tracked": 0}

        avg_amplifier = np.mean([s.disease_amplifier for s in self._contact_states.values()])
        avg_shock = np.mean([s.cultural_shock for s in self._contact_states.values()])

        contacts = sum(len(s.contact_history) for s in self._contact_states.values())
        syncretism = sum(len(s.syncretic_blends) for s in self._contact_states.values())

        return {
            "total_tracked": len(self._contact_states),
            "avg_disease_amplifier": avg_amplifier,
            "avg_cultural_shock": avg_shock,
            "total_contacts": contacts,
            "total_syncretic_blends": syncretism,
        }
