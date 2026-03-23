from ..systems.base import System
from ..types import TickContext, WorldEvent, EventType, Agent
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class PhilosophyState:
    agent_id: str
    philosophical_school: str = "none"
    worldview_coherence: float = 0.0
    norm_alignment: Dict[str, float] = field(default_factory=dict)
    ethical_framework: List[str] = field(default_factory=list)
    metaphysical_beliefs: List[str] = field(default_factory=list)


class PhilosophySystem(System):
    def __init__(self, world):
        super().__init__(world)
        self._philosophy_states: Dict[str, PhilosophyState] = {}
        self._emergence_threshold = 0.7

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.social_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        events = []

        for agent in self.world.agents.values():
            if not agent.is_alive or agent.neural_complexity < 2:
                continue

            state = self._get_or_create_state(agent)
            self._emergent_philosophical_schools(agent, state, ctx, events)
            self._norm_emergence(agent, state, ctx)
            self._worldview_formation(agent, state)

        return events

    def _get_or_create_state(self, agent: Agent) -> PhilosophyState:
        if agent.id not in self._philosophy_states:
            self._philosophy_states[agent.id] = PhilosophyState(agent_id=agent.id)
        return self._philosophy_states[agent.id]

    def _emergent_philosophical_schools(
        self, agent: Agent, state: PhilosophyState, ctx: TickContext, events: List[WorldEvent]
    ):
        if agent.neural_complexity < 3:
            return

        uncertainty = 1.0 - agent.emotion.trust

        if (
            uncertainty > self._emergence_threshold
            or state.worldview_coherence > self._emergence_threshold
        ):
            schools_proneness = self._assess_school_proneness(agent, state)

            if np.random.random() < schools_proneness * 0.01:
                new_school = self._select_philosophical_school(agent, state)

                if state.philosophical_school != new_school:
                    state.philosophical_school = new_school
                    events.append(
                        WorldEvent(
                            tick=ctx.tick,
                            type=EventType.GOD_MODE_INTERVENTION,
                            data={"philosophical_school": new_school},
                            source_id=agent.id,
                        )
                    )

    def _assess_school_proneness(self, agent: Agent, state: PhilosophyState) -> float:
        proneness = 0.0

        if agent.neural_complexity > 4:
            proneness += 0.3

        if agent.health < 0.3:
            proneness += 0.2

        social_iso = agent.emotion.trust < 0.3
        if social_iso:
            proneness += 0.2

        if hasattr(self.world, "culture"):
            culture_state = self.world.culture._culture_states.get(agent.id)
            if culture_state and len(culture_state.belief_system) > 0:
                proneness += 0.3

        return min(1.0, proneness)

    def _select_philosophical_school(self, agent: Agent, state: PhilosophyState) -> str:
        materialist_score = 0.0
        idealist_score = 0.0
        determinist_score = 0.0

        if agent.health > 0.7:
            materialist_score += 0.3

        if agent.neural_complexity > 4:
            idealist_score += 0.3

        if agent.emotion.fear > 0.6:
            determinist_score += 0.3

        if hasattr(self.world, "stress"):
            stress_state = self.world.stress._stress_states.get(agent.id)
            if stress_state and stress_state.allostatic_load > 1.5:
                determinist_score += 0.3

        scores = {
            "materialism": materialist_score,
            "idealism": idealist_score,
            "determinism": determinist_score,
        }

        return max(scores, key=scores.get)

    def _norm_emergence(self, agent: Agent, state: PhilosophyState, ctx: TickContext):
        if agent.neural_complexity < 3 or not agent.group_id:
            return

        experience = agent.neural_complexity * 0.1
        social_influence = agent.emotion.trust * agent.emotion.joy

        norm_candidates = [
            (" reciprocity", 0.5),
            ("justice", 0.4),
            ("fairness", 0.4),
            ("loyalty", 0.3),
            ("protection", 0.3),
        ]

        for norm, base_val in norm_candidates:
            if norm not in state.norm_alignment:
                if np.random.random() < (experience + social_influence) * base_val * 0.01:
                    state.norm_alignment[norm] = base_val

    def _worldview_formation(self, agent: Agent, state: PhilosophyState):
        coherence = 0.0

        if state.philosophical_school != "none":
            coherence += 0.4

        if len(state.ethical_framework) > 0:
            coherence += 0.2

        if len(state.norm_alignment) > 2:
            coherence += 0.3

        state.worldview_coherence = min(1.0, coherence)

        if agent.emotion.trust > 0.7 and agent.emotion.joy > 0.5:
            agent.emotion.anticipation = min(
                1.0, agent.emotion.anticipation + state.worldview_coherence * 0.05
            )

    def get_philosophy_stats(self) -> Dict:
        if not self._philosophy_states:
            return {"total_tracked": 0}

        avg_coherence = np.mean([s.worldview_coherence for s in self._philosophy_states.values()])
        schools = {}
        for s in self._philosophy_states.values():
            if s.philosophical_school != "none":
                schools[s.philosophical_school] = schools.get(s.philosophical_school, 0) + 1

        return {
            "total_tracked": len(self._philosophy_states),
            "avg_worldview_coherence": avg_coherence,
            "school_distribution": schools,
        }
