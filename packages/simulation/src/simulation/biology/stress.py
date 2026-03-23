from ..systems.base import System
from ..types import TickContext, WorldEvent, EventType, Agent
import numpy as np
from dataclasses import dataclass
from typing import Dict


@dataclass
class StressState:
    agent_id: str
    cortisol_level: float = 0.0
    allostatic_load: float = 0.0
    cognitive_load: float = 0.0
    is_acutely_stressed: bool = False
    trauma_history: list[int] = None

    def __post_init__(self):
        if self.trauma_history is None:
            self.trauma_history = []


class StressSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self._stress_states: Dict[str, StressState] = {}
        self._hppa_axis_gain = 2.5
        self._allostatic_decay = 0.01
        self._max_allostatic = 5.0

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.biology_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        events = []

        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue

            state = self._get_or_create_state(agent)

            acute_stressors = self._compute_acute_stressors(agent)
            chronic_stressors = self._compute_chronic_stressors(agent)

            state.cortisol_level = self._activate_hpa_axis(
                state.cortisol_level, acute_stressors, chronic_stressors
            )

            state.allostatic_load += self._compute_allostatic_load(
                agent, state.cortisol_level, chronic_stressors
            )
            state.allostatic_load = max(0, state.allostatic_load - self._allostatic_decay)
            state.allostatic_load = min(state.allostatic_load, self._max_allostatic)

            state.cognitive_load = self._compute_cognitive_load(agent, state)

            state.is_acutely_stressed = state.cortisol_level > 1.5

            self._apply_stress_effects(agent, state)

            if state.cortisol_level > 2.0 and np.random.random() < 0.01:
                state.trauma_history.append(ctx.tick)

            if len(state.trauma_history) > 20:
                state.trauma_history = state.trauma_history[-20:]

        return events

    def _get_or_create_state(self, agent: Agent) -> StressState:
        if agent.id not in self._stress_states:
            self._stress_states[agent.id] = StressState(agent_id=agent.id)
        return self._stress_states[agent.id]

    def _compute_acute_stressors(self, agent: Agent) -> float:
        stressors = 0.0
        personality = getattr(agent, "personality", None)

        if agent.health < 0.5:
            base_threat = (0.5 - agent.health) * 2.0
            if personality and personality.neuroticism > 0.5:
                base_threat *= 1.0 + personality.neuroticism * 0.3
            stressors += base_threat

        if agent.energy < 0.2:
            base_energy = (0.2 - agent.energy) * 1.5
            if personality and personality.neuroticism > 0.5:
                base_energy *= 1.0 + personality.neuroticism * 0.2
            stressors += base_energy

        if agent.pathogen_exposure > 0.5:
            stressors += agent.inflammation_level * 0.8

        predator_nearby = self._count_potential_threats(agent)
        if predator_nearby > 0:
            threat_response = min(1.0, predator_nearby * 0.3)
            if personality:
                if personality.neuroticism > 0.5:
                    threat_response *= 1.0 + personality.neuroticism * 0.4
                elif personality.neuroticism < 0.3:
                    threat_response *= 0.7 + personality.neuroticism * 0.3
            stressors += threat_response

        if agent.stage.value == "neonatal" and agent.group_id is None:
            stressors += 0.5

        return min(3.0, stressors)

    def _compute_chronic_stressors(self, agent: Agent) -> float:
        chronic = 0.0

        state = self._stress_states.get(agent.id)
        if state and len(state.trauma_history) > 3:
            chronic += min(1.0, len(state.trauma_history) * 0.1)

        if agent.group_id:
            group_members = sum(
                1 for a in self.world.agents.values() if a.group_id == agent.group_id and a.is_alive
            )
            if group_members < 3:
                chronic += 0.2

        if agent.stage.value == "elder":
            chronic += 0.3

        if agent.neural_complexity > 3:
            chronic += agent.neural_complexity * 0.05

        return chronic

    def _activate_hpa_axis(self, current_cortisol: float, acute: float, chronic: float) -> float:
        stimulus = (acute * self._hppa_axis_gain) + (chronic * 0.5)

        cortisol_response = current_cortisol + stimulus * 0.1

        negative_feedback = current_cortisol * 0.05
        cortisol_response -= negative_feedback

        return max(0.0, min(3.0, cortisol_response))

    def _compute_allostatic_load(self, agent: Agent, cortisol: float, chronic: float) -> float:
        if agent.neural_complexity < 2:
            return 0.0

        load_increase = (cortisol * 0.05) + (chronic * 0.02)

        sleep_debt = 0.0
        if hasattr(self.world, "sleep"):
            is_sleeping = self.world.sleep.is_agent_sleeping(agent.id)
            if not is_sleeping:
                sleep_debt = 0.01

        return load_increase + sleep_debt

    def _compute_cognitive_load(self, agent: Agent, state: StressState) -> float:
        if agent.neural_complexity < 2:
            return 0.0

        base_load = agent.neural_complexity * 0.05

        social_load = 0.0
        if agent.group_id:
            members = sum(
                1 for a in self.world.agents.values() if a.group_id == agent.group_id and a.is_alive
            )
            if members > 5:
                social_load = (members - 5) * 0.02

        stress_load = state.allostatic_load * 0.1

        memory_load = 0.0
        if agent.memory:
            memory_load = len(agent.memory.working_memory) * 0.05

        return min(1.0, base_load + social_load + stress_load + memory_load)

    def _apply_stress_effects(self, agent: Agent, state: StressState):
        personality = getattr(agent, "personality", None)

        if state.is_acutely_stressed:
            fear_increase = 0.1
            anger_increase = 0.05
            sadness_increase = 0.03

            if personality:
                if personality.neuroticism > 0.5:
                    fear_increase *= 1.0 + personality.neuroticism * 0.5
                    anger_increase *= 1.0 + personality.neuroticism * 0.3
                elif personality.neuroticism < 0.3:
                    fear_increase *= 0.7
                    anger_increase *= 0.7

                if personality.conscientiousness > 0.5:
                    fear_increase *= 0.8

                if personality.openness > 0.5:
                    anger_increase *= 0.9

            agent.emotion.fear = min(1.0, agent.emotion.fear + fear_increase)
            agent.emotion.anger = min(1.0, agent.emotion.anger + anger_increase)
            agent.emotion.sadness = min(1.0, agent.emotion.sadness + sadness_increase)

            if agent.neural_complexity > 2 and agent.memory:
                memory_loss_prob = 0.2
                if personality and personality.conscientiousness > 0.5:
                    memory_loss_prob *= 0.7
                if np.random.random() < state.cognitive_load * memory_loss_prob:
                    if len(agent.memory.working_memory) > 0:
                        idx = np.random.randint(0, len(agent.memory.working_memory))
                        agent.memory.working_memory.pop(idx)

        if state.allostatic_load > 1.0:
            health_damage = state.allostatic_load * 0.005
            energy_damage = state.allostatic_load * 0.003

            if personality:
                if personality.conscientiousness > 0.5:
                    health_damage *= 0.85
                    energy_damage *= 0.85
                if personality.neuroticism > 0.6:
                    health_damage *= 1.0 + personality.neuroticism * 0.2
                if personality.openness > 0.5:
                    health_damage *= 0.9

            agent.health = max(0, agent.health - health_damage)
            agent.energy = max(0, agent.energy - energy_damage)

            agent.emotion.sadness = min(1.0, agent.emotion.sadness + state.allostatic_load * 0.02)
            agent.emotion.joy = max(0.0, agent.emotion.joy - state.allostatic_load * 0.02)

        if state.cognitive_load > 0.5:
            trust_decay = 0.05
            if personality and personality.agreeableness > 0.5:
                trust_decay *= 0.7
            if np.random.random() < state.cognitive_load * 0.2:
                agent.emotion.trust = max(0.0, agent.emotion.trust - trust_decay)

        if len(state.trauma_history) > 5:
            trauma_rate = len(state.trauma_history) * 0.002
            trauma_multiplier = 1.0
            if personality:
                if personality.neuroticism > 0.5:
                    trauma_multiplier *= 1.0 + personality.neuroticism * 0.3
                if personality.openness > 0.5:
                    trauma_multiplier *= 0.85
                if personality.conscientiousness > 0.5:
                    trauma_multiplier *= 0.9
            agent.emotion.fear = min(1.0, agent.emotion.fear + trauma_rate * trauma_multiplier)

        if agent.health < 0.2:
            agent.emotion.sadness = min(1.0, agent.emotion.sadness + 0.2)
            agent.emotion.trust = max(0.0, agent.emotion.trust - 0.1)

    def _count_potential_threats(self, agent: Agent) -> int:
        count = 0
        for other in self.world.agents.values():
            if other.id == agent.id or not other.is_alive:
                continue
            dx = other.position.x - agent.position.x
            dy = other.position.y - agent.position.y
            dist = (dx**2 + dy**2) ** 0.5
            if dist < agent.sensory_range * 0.5:
                if (
                    other.energy > agent.energy
                    and other.neural_complexity >= agent.neural_complexity
                ):
                    count += 1
        return count

    def get_stress_stats(self) -> Dict:
        all_loads = [s.allostatic_load for s in self._stress_states.values()]
        all_cortisol = [s.cortisol_level for s in self._stress_states.values()]

        stressed = sum(1 for s in self._stress_states.values() if s.is_acutely_stressed)
        traumatized = sum(1 for s in self._stress_states.values() if len(s.trauma_history) > 3)

        return {
            "total_tracked": len(self._stress_states),
            "acutely_stressed": stressed,
            "traumatized": traumatized,
            "avg_allostatic_load": np.mean(all_loads) if all_loads else 0.0,
            "avg_cortisol": np.mean(all_cortisol) if all_cortisol else 0.0,
        }
