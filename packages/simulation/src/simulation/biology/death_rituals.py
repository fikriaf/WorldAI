from ..systems.base import System
from ..types import TickContext, WorldEvent, EventType, Agent
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class DeathRitualState:
    agent_id: str
    performed_rituals: List[str] = field(default_factory=list)
    ancestor_memories: List[Dict] = field(default_factory=list)
    legacy_contributions: float = 0.0
    inheritance_claims: List[Dict] = field(default_factory=list)


class DeathRitualsSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self._ritual_states: Dict[str, DeathRitualState] = {}
        self._memory_decay = 0.01
        self._legacy_threshold = 0.3

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.social_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        events = []
        self._process_deaths(ctx, events)

        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue

            state = self._get_or_create_state(agent)
            self._acknowledge_mortality(agent, state, ctx)
            self._build_legacy(agent, state, ctx, events)
            self._maintain_ancestor_memory(agent, state, ctx)

        return events

    def _get_or_create_state(self, agent: Agent) -> DeathRitualState:
        if agent.id not in self._ritual_states:
            self._ritual_states[agent.id] = DeathRitualState(agent_id=agent.id)
        return self._ritual_states[agent.id]

    def _process_deaths(self, ctx: TickContext, events: List[WorldEvent]):
        dead_agents = [a for a in self.world.agents.values() if not a.is_alive]

        for dead in dead_agents:
            state = self._get_or_create_state(dead)
            if not state.performed_rituals and dead.group_id:
                self._perform_death_ritual(dead, state, ctx, events)

            self._transfer_inheritance(dead, state, ctx, events)

    def _perform_death_ritual(
        self, agent: Agent, state: DeathRitualState, ctx: TickContext, events: List[WorldEvent]
    ):
        group_members = [
            a for a in self.world.agents.values() if a.group_id == agent.group_id and a.is_alive
        ]

        if len(group_members) >= 2:
            ritual_types = ["burial", "memorial", "vigil", "celebration_of_life"]
            ritual = np.random.choice(ritual_types)
            state.performed_rituals.append(ritual)

            for member in group_members:
                member_state = self._get_or_create_state(member)
                member_state.ancestor_memories.append(
                    {
                        "ancestor_id": agent.id,
                        "tick": ctx.tick,
                        "ritual_type": ritual,
                        "memory_strength": 1.0,
                    }
                )

            events.append(
                WorldEvent(
                    tick=ctx.tick,
                    type=EventType.GOD_MODE_INTERVENTION,
                    data={"death_ritual": ritual, "deceased_id": agent.id},
                    source_id=agent.group_id,
                )
            )

    def _transfer_inheritance(
        self, agent: Agent, state: DeathRitualState, ctx: TickContext, events: List[WorldEvent]
    ):
        if not agent.group_id:
            return

        group_members = [
            a
            for a in self.world.agents.values()
            if a.group_id == agent.group_id and a.is_alive and a.id != agent.id
        ]

        if not group_members:
            return

        wealth = getattr(agent, "economy_wealth", 0.5)
        if wealth > 0:
            inheritance_portion = wealth / len(group_members)

            for heir in group_members:
                heir_wealth = getattr(heir, "economy_wealth", 0.5)
                setattr(heir, "economy_wealth", heir_wealth + inheritance_portion * 0.5)

                state.inheritance_claims.append(
                    {"heir_id": heir.id, "amount": inheritance_portion * 0.5, "tick": ctx.tick}
                )

    def _acknowledge_mortality(self, agent: Agent, state: DeathRitualState, ctx: TickContext):
        if agent.stage.value in ["adult", "elder"] and agent.neural_complexity > 2:
            if agent.health < 0.3:
                agent.emotion.fear = min(1.0, agent.emotion.fear + 0.05)
                agent.emotion.sadness = min(1.0, agent.emotion.sadness + 0.03)

            death_awareness = (1.0 - agent.health) * 0.1
            if death_awareness > 0.2 and agent.emotion.trust > 0.3:
                if len(state.ancestor_memories) > 0:
                    agent.emotion.anticipation = min(1.0, agent.emotion.anticipation + 0.02)

    def _build_legacy(
        self, agent: Agent, state: DeathRitualState, ctx: TickContext, events: List[WorldEvent]
    ):
        if agent.neural_complexity < 2:
            return

        knowledge_contribution = agent.neural_complexity * 0.01
        social_contribution = agent.emotion.joy * agent.emotion.trust * 0.02

        state.legacy_contributions += knowledge_contribution + social_contribution

        if state.legacy_contributions > self._legacy_threshold and len(state.performed_rituals) > 0:
            if agent.group_id:
                events.append(
                    WorldEvent(
                        tick=ctx.tick,
                        type=EventType.GOD_MODE_INTERVENTION,
                        data={"legacy_established": True},
                        source_id=agent.id,
                    )
                )

        if agent.stage.value == "elder":
            state.legacy_contributions *= 1.05

    def _maintain_ancestor_memory(self, agent: Agent, state: DeathRitualState, ctx: TickContext):
        for ancestor in state.ancestor_memories:
            ancestor["memory_strength"] = max(0, ancestor["memory_strength"] - self._memory_decay)

        state.ancestor_memories = [a for a in state.ancestor_memories if a["memory_strength"] > 0.1]

        if len(state.ancestor_memories) > 0:
            avg_memory = np.mean([a["memory_strength"] for a in state.ancestor_memories])
            if avg_memory > 0.5:
                agent.emotion.trust = min(1.0, agent.emotion.trust + 0.02)

    def get_death_ritual_stats(self) -> Dict:
        if not self._ritual_states:
            return {"total_tracked": 0}

        total_rituals = sum(len(s.performed_rituals) for s in self._ritual_states.values())
        avg_legacy = np.mean([s.legacy_contributions for s in self._ritual_states.values()])

        alive_states = [
            s
            for s in self._ritual_states.values()
            if self.world.agents.get(s.agent_id) and self.world.agents[s.agent_id].is_alive
        ]
        alive_ancestors = sum(len(s.ancestor_memories) for s in alive_states)

        return {
            "total_tracked": len(self._ritual_states),
            "total_rituals_performed": total_rituals,
            "avg_legacy_contributions": avg_legacy,
            "alive_with_ancestor_memories": len([s for s in alive_states if s.ancestor_memories]),
            "total_ancestor_memories": alive_ancestors,
        }
