from ..systems.base import System
from ..types import TickContext, WorldEvent, EventType, Agent
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass
class MisinformationState:
    agent_id: str
    believed_narratives: Set[str] = field(default_factory=set)
    misinformation_exposure: float = 0.0
    confirmation_bias: float = 0.3
    epistemic_bubble_homogeneity: float = 0.0
    truth_sensitivity: float = 0.8


class MisinformationSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self._misinfo_states: Dict[str, MisinformationState] = {}
        self._infection_rate = 0.05
        self._recovery_rate = 0.01
        self._bubble_formation_threshold = 0.7

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.social_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        events = []

        self._propagate_information(ctx, events)
        self._form_epistemic_bubbles(ctx)

        for agent in self.world.agents.values():
            if not agent.is_alive or agent.neural_complexity < 2:
                continue

            state = self._get_or_create_state(agent)
            self._apply_confirmation_bias(agent, state)
            self._epistemic_warfare(agent, state, ctx, events)
            self._apply_misinfo_effects(agent, state)

        return events

    def _get_or_create_state(self, agent: Agent) -> MisinformationState:
        if agent.id not in self._misinfo_states:
            self._misinfo_states[agent.id] = MisinformationState(agent_id=agent.id)
        return self._misinfo_states[agent.id]

    def _propagate_information(self, ctx: TickContext, events: List[WorldEvent]):
        if not hasattr(self.world, "communication"):
            return

        for agent in self.world.agents.values():
            if not agent.is_alive or agent.neural_complexity < 2:
                continue

            state = self._get_or_create_state(agent)

            if agent.group_id:
                group_members = [
                    a
                    for a in self.world.agents.values()
                    if a.group_id == agent.group_id and a.id != agent.id and a.is_alive
                ]

                for member in group_members:
                    member_state = self._get_or_create_state(member)

                    if len(member_state.believed_narratives) > 0:
                        narrative = list(member_state.believed_narratives)[0]

                        if np.random.random() < self._infection_rate * state.confirmation_bias:
                            state.believed_narratives.add(narrative)
                            state.misinformation_exposure = min(
                                1.0, state.misinformation_exposure + 0.05
                            )

    def _form_epistemic_bubbles(self, ctx: TickContext):
        for agent in self.world.agents.values():
            if not agent.is_alive or not agent.group_id:
                continue

            state = self._get_or_create_state(agent)

            if len(state.believed_narratives) < 2:
                continue

            group_members = [
                a for a in self.world.agents.values() if a.group_id == agent.group_id and a.is_alive
            ]

            if len(group_members) < 3:
                continue

            bubble_narratives = []
            for member in group_members:
                member_state = self._get_or_create_state(member)
                bubble_narratives.extend(member_state.believed_narratives)

            if bubble_narratives:
                unique_narratives = set(bubble_narratives)
                homogeneity = 1.0 - (len(unique_narratives) / len(bubble_narratives))

                if homogeneity > self._bubble_formation_threshold:
                    state.epistemic_bubble_homogeneity = min(
                        1.0, state.epistemic_bubble_homogeneity + 0.1
                    )

    def _apply_confirmation_bias(self, agent: Agent, state: MisinformationState):
        if agent.emotion.anger > 0.6:
            state.confirmation_bias = min(1.0, state.confirmation_bias + 0.05)

        if agent.emotion.fear > 0.6:
            state.confirmation_bias = min(1.0, state.confirmation_bias + 0.03)

        if agent.emotion.trust > 0.6:
            state.truth_sensitivity = min(1.0, state.truth_sensitivity + 0.02)

        if agent.stage.value == "elder" and agent.neural_complexity > 3:
            state.confirmation_bias = min(1.0, state.confirmation_bias + 0.01)

    def _epistemic_warfare(
        self, agent: Agent, state: MisinformationState, ctx: TickContext, events: List[WorldEvent]
    ):
        if not agent.group_id:
            return

        if agent.emotion.anger > 0.7 and agent.neural_complexity > 3:
            other_groups = [
                a for a in self.world.agents.values() if a.group_id != agent.group_id and a.is_alive
            ]

            for other in other_groups[:3]:
                other_state = self._get_or_create_state(other)
                if np.random.random() < 0.01:
                    other_state.misinformation_exposure = min(
                        1.0, other_state.misinformation_exposure + 0.1
                    )

                    events.append(
                        WorldEvent(
                            tick=ctx.tick,
                            type=EventType.GOD_MODE_INTERVENTION,
                            data={"epistemic_attack": True},
                            source_id=agent.id,
                            target_id=other.id,
                        )
                    )

    def _apply_misinfo_effects(self, agent: Agent, state: MisinformationState):
        if state.misinformation_exposure > 0.5:
            agent.emotion.trust = max(
                0.0, agent.emotion.trust - state.misinformation_exposure * 0.05
            )
            agent.emotion.fear = min(1.0, agent.emotion.fear + state.misinformation_exposure * 0.03)

        if state.epistemic_bubble_homogeneity > 0.8:
            agent.emotion.anger = min(1.0, agent.emotion.anger + 0.05)
            agent.emotion.trust = max(0.0, agent.emotion.trust - 0.1)

        if np.random.random() < self._recovery_rate * state.truth_sensitivity:
            if state.believed_narratives and len(state.believed_narratives) > 0:
                state.believed_narratives.pop()

    def get_misinfo_stats(self) -> Dict:
        if not self._misinfo_states:
            return {"total_tracked": 0}

        avg_exposure = np.mean([s.misinformation_exposure for s in self._misinfo_states.values()])
        avg_bias = np.mean([s.confirmation_bias for s in self._misinfo_states.values()])

        return {
            "total_tracked": len(self._misinfo_states),
            "avg_misinformation_exposure": avg_exposure,
            "avg_confirmation_bias": avg_bias,
            "total_believed_narratives": sum(
                len(s.believed_narratives) for s in self._misinfo_states.values()
            ),
        }
