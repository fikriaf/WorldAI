from ..systems.base import System
from ..types import TickContext, WorldEvent, Agent, AgentID
import numpy as np
from dataclasses import dataclass
from typing import Dict


@dataclass
class MentalHealthState:
    agent_id: str
    depression_score: float = 0.0
    anxiety_score: float = 0.0
    psychosis_score: float = 0.0
    dissociation_level: float = 0.0
    mania_score: float = 0.0
    disorder_episodes: int = 0
    resilience: float = 0.5


class MentalHealthSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self._mental_health: Dict[str, MentalHealthState] = {}
        self._resilience_recovery_rate = 0.005

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.biology_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        events = []

        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue
            if agent.neural_complexity < 2:
                continue

            state = self._get_or_create_state(agent)

            self._update_depression(agent, state)
            self._update_anxiety(agent, state)
            self._update_psychosis(agent, state)
            self._update_mania(agent, state)
            self._update_dissociation(agent, state)
            self._update_resilience(agent, state)

        return events

    def _get_or_create_state(self, agent: Agent) -> MentalHealthState:
        if agent.id not in self._mental_health:
            self._mental_health[agent.id] = MentalHealthState(agent_id=agent.id)
        return self._mental_health[agent.id]

    def _update_depression(self, agent: Agent, state: MentalHealthState):
        depressors = 0.0

        if agent.emotion.sadness > 0.6:
            depressors += agent.emotion.sadness * 0.3

        if agent.health < 0.3:
            depressors += (0.3 - agent.health) * 0.5

        if agent.energy < 0.2:
            depressors += (0.2 - agent.energy) * 0.3

        if hasattr(self.world, "stress"):
            stress_state = self.world.stress._stress_states.get(agent.id)
            if stress_state:
                depressors += stress_state.allostatic_load * 0.1

        if not agent.group_id and agent.neural_complexity > 2:
            depressors += 0.1

        state.depression_score += depressors * 0.05

        resilience_factor = state.resilience * self._resilience_recovery_rate
        recovery = 0.02 * (1.0 + agent.emotion.joy) * resilience_factor
        state.depression_score = max(0.0, state.depression_score - recovery)

        state.depression_score = min(1.0, max(0.0, state.depression_score))

        if state.depression_score > 0.7:
            agent.emotion.joy = max(0.0, agent.emotion.joy - 0.05)
            agent.emotion.sadness = min(1.0, agent.emotion.sadness + 0.05)
            agent.energy = max(0, agent.energy - 0.01)

    def _update_anxiety(self, agent: Agent, state: MentalHealthState):
        anxiety_sources = 0.0

        if agent.emotion.fear > 0.5:
            anxiety_sources += agent.emotion.fear * 0.3

        if hasattr(self.world, "stress"):
            stress_state = self.world.stress._stress_states.get(agent.id)
            if stress_state:
                anxiety_sources += stress_state.cortisol_level * 0.1
                if stress_state.is_acutely_stressed:
                    anxiety_sources += 0.2

        if agent.pathogen_exposure > 0.5:
            anxiety_sources += agent.inflammation_level * 0.2

        if agent.neural_complexity > 3:
            anxiety_sources += agent.neural_complexity * 0.02

        state.anxiety_score += anxiety_sources * 0.05

        safety_signals = 0.0
        if agent.group_id:
            safety_signals += 0.1
        if agent.health > 0.7:
            safety_signals += 0.1
        if agent.energy > 0.5:
            safety_signals += 0.1

        recovery = safety_signals * 0.02 * state.resilience
        state.anxiety_score = max(0.0, state.anxiety_score - recovery)

        state.anxiety_score = min(1.0, max(0.0, state.anxiety_score))

        if state.anxiety_score > 0.6:
            agent.emotion.fear = min(1.0, agent.emotion.fear + 0.03)

    def _update_psychosis(self, agent: Agent, state: MentalHealthState):
        psychosis_risk = 0.0

        if agent.health < 0.1:
            psychosis_risk += (0.1 - agent.health) * 2.0

        if hasattr(self.world, "stress"):
            stress_state = self.world.stress._stress_states.get(agent.id)
            if stress_state and stress_state.cortisol_level > 2.0:
                psychosis_risk += 0.2

        if agent.stage.value == "elder":
            psychosis_risk += 0.1

        if agent.neural_complexity > 5:
            psychosis_risk += agent.neural_complexity * 0.02

        state.psychosis_score += psychosis_risk * 0.02

        reality_check = 0.0
        if agent.group_id:
            reality_check += 0.02
        if agent.memory:
            reality_check += min(0.05, len(agent.memory.working_memory) * 0.01)

        state.psychosis_score = max(0.0, state.psychosis_score - reality_check * state.resilience)

        state.psychosis_score = min(1.0, max(0.0, state.psychosis_score))

        if state.psychosis_score > 0.5:
            agent.emotion.surprise = min(1.0, agent.emotion.surprise + 0.02)

    def _update_mania(self, agent: Agent, state: MentalHealthState):
        mania_triggers = 0.0

        if agent.emotion.joy > 0.9:
            mania_triggers += (agent.emotion.joy - 0.9) * 2.0

        if hasattr(self.world, "stress"):
            stress_state = self.world.stress._stress_states.get(agent.id)
            if (
                stress_state
                and stress_state.trauma_history
                and len(stress_state.trauma_history) > 5
            ):
                mania_triggers += 0.1

        state.mania_score += mania_triggers * 0.03

        if agent.health < 0.5:
            state.mania_score = max(0.0, state.mania_score - 0.02)

        state.mania_score = min(1.0, max(0.0, state.mania_score))

        if state.mania_score > 0.7:
            agent.emotion.joy = min(1.0, agent.emotion.joy + 0.1)
            agent.emotion.anger = min(1.0, agent.emotion.anger + 0.05)
            agent.emotion.trust = min(1.0, agent.emotion.trust + 0.1)

    def _update_dissociation(self, agent: Agent, state: MentalHealthState):
        if agent.neural_complexity < 3:
            return

        dissociation_triggers = 0.0

        if hasattr(self.world, "stress"):
            stress_state = self.world.stress._stress_states.get(agent.id)
            if stress_state and len(stress_state.trauma_history) > 3:
                dissociation_triggers += 0.05 * len(stress_state.trauma_history)

        if state.depression_score > 0.7:
            dissociation_triggers += 0.02

        state.dissociation_level += dissociation_triggers * 0.05

        recovery = self._resilience_recovery_rate * state.resilience
        state.dissociation_level = max(0.0, state.dissociation_level - recovery)

        state.dissociation_level = min(1.0, max(0.0, state.dissociation_level))

        if state.dissociation_level > 0.5:
            if np.random.random() < state.dissociation_level * 0.1:
                if agent.memory and agent.memory.working_memory:
                    idx = np.random.randint(0, len(agent.memory.working_memory))
                    agent.memory.working_memory.pop(idx)

    def _update_resilience(self, agent: Agent, state: MentalHealthState):
        resilience_boost = 0.0

        if agent.group_id:
            resilience_boost += 0.02
        if agent.health > 0.8:
            resilience_boost += 0.01
        if agent.energy > 0.7:
            resilience_boost += 0.01
        if agent.stage.value == "adult":
            resilience_boost += 0.01

        if hasattr(self.world, "play"):
            skills = self.world.play.get_skill_levels(agent.id)
            if skills.get("social", 0) > 0.3:
                resilience_boost += 0.02

        state.resilience = min(1.0, state.resilience + resilience_boost)

        if agent.health < 0.3:
            state.resilience = max(0.1, state.resilience - 0.01)

    def get_mental_health_stats(self) -> Dict:
        if not self._mental_health:
            return {
                "depressed": 0,
                "anxious": 0,
                "psychotic": 0,
                "manic": 0,
                "dissociating": 0,
            }

        return {
            "depressed": sum(1 for s in self._mental_health.values() if s.depression_score > 0.6),
            "anxious": sum(1 for s in self._mental_health.values() if s.anxiety_score > 0.6),
            "psychotic": sum(1 for s in self._mental_health.values() if s.psychosis_score > 0.5),
            "manic": sum(1 for s in self._mental_health.values() if s.mania_score > 0.7),
            "dissociating": sum(
                1 for s in self._mental_health.values() if s.dissociation_level > 0.5
            ),
            "avg_resilience": float(np.mean([s.resilience for s in self._mental_health.values()])),
            "avg_depression": float(
                np.mean([s.depression_score for s in self._mental_health.values()])
            ),
            "avg_anxiety": float(np.mean([s.anxiety_score for s in self._mental_health.values()])),
        }
