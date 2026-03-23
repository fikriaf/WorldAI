from ..systems.base import System
from ..types import TickContext, WorldEvent, Agent, AgentID
import numpy as np
from dataclasses import dataclass
from typing import Dict


@dataclass
class AddictionState:
    agent_id: str
    tolerance_level: float = 0.0
    withdrawal_strength: float = 0.0
    craving_intensity: float = 0.0
    exposure_history: list[float] = None
    is_dependent: bool = False

    def __post_init__(self):
        if self.exposure_history is None:
            self.exposure_history = []


class AddictionSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self._addiction_states: Dict[str, AddictionState] = {}
        self._superstimuli_sources = ["energy_rich", "social_bonding", "play_reward"]
        self._base_addiction_rate = 0.001

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

            exposure = self._measure_exposure(agent, ctx)
            self._update_tolerance(state, exposure)
            self._update_withdrawal(state, agent, ctx)
            self._update_craving(state, exposure)
            self._apply_addiction_effects(agent, state)

            state.exposure_history.append(exposure)
            if len(state.exposure_history) > 100:
                state.exposure_history = state.exposure_history[-100:]

        return events

    def _get_or_create_state(self, agent: Agent) -> AddictionState:
        if agent.id not in self._addiction_states:
            self._addiction_states[agent.id] = AddictionState(agent_id=agent.id)
        return self._addiction_states[agent.id]

    def _measure_exposure(self, agent: Agent, ctx: TickContext) -> float:
        exposure = 0.0

        if hasattr(self.world, "play"):
            play_stats = self.world.play.get_play_stats()
            if play_stats.get("active_sessions", 0) > 0:
                exposure += 0.3

        if hasattr(self.world, "economy"):
            eco_stats = self.world.economy.get_economy_stats()
            if eco_stats.get("total_exchanges", 0) > 0:
                exposure += 0.1

        if agent.emotion.joy > 0.8:
            exposure += (agent.emotion.joy - 0.8) * 1.5

        if agent.group_id:
            members = sum(
                1 for a in self.world.agents.values() if a.group_id == agent.group_id and a.is_alive
            )
            if members > 5:
                exposure += 0.2

        return min(2.0, exposure)

    def _update_tolerance(self, state: AddictionState, exposure: float):
        state.tolerance_level += exposure * self._base_addiction_rate * 10

        if len(state.exposure_history) > 10:
            recent = state.exposure_history[-10:]
            avg = sum(recent) / len(recent)
            if avg > 0.5:
                state.tolerance_level += 0.01

        state.tolerance_level = max(0.0, min(3.0, state.tolerance_level))

    def _update_withdrawal(self, state: AddictionState, agent: Agent, ctx: TickContext):
        if not state.is_dependent:
            if state.tolerance_level > 1.5:
                state.is_dependent = True
            return

        recent_exposure = state.exposure_history[-5:] if state.exposure_history else []
        avg_recent = sum(recent_exposure) / max(1, len(recent_exposure))

        if avg_recent < 0.2:
            state.withdrawal_strength = min(
                1.0, state.withdrawal_strength + 0.05 * state.tolerance_level
            )
        else:
            state.withdrawal_strength = max(0.0, state.withdrawal_strength - 0.02)

        if state.tolerance_level < 0.5:
            state.is_dependent = False

    def _update_craving(self, state: AddictionState, exposure: float):
        if not state.is_dependent:
            if state.tolerance_level > 0.5:
                state.craving_intensity = state.tolerance_level * 0.3
            return

        recent_exposure = state.exposure_history[-10:] if state.exposure_history else []
        avg_recent = sum(recent_exposure) / max(1, len(recent_exposure))

        if avg_recent < 0.3:
            state.craving_intensity = min(
                1.0,
                state.craving_intensity
                + state.tolerance_level * 0.05
                + state.withdrawal_strength * 0.1,
            )
        else:
            state.craving_intensity = max(0.0, state.craving_intensity - 0.03 * avg_recent)

    def _apply_addiction_effects(self, agent: Agent, state: AddictionState):
        if state.craving_intensity > 0.5:
            agent.emotion.anger = min(1.0, agent.emotion.anger + state.craving_intensity * 0.05)
            agent.emotion.sadness = min(1.0, agent.emotion.sadness + state.craving_intensity * 0.03)

            if state.craving_intensity > 0.7:
                agent.emotion.fear = min(1.0, agent.emotion.fear + 0.02)

        if state.withdrawal_strength > 0.3:
            agent.health = max(0, agent.health - state.withdrawal_strength * 0.01)
            agent.energy = max(0, agent.energy - state.withdrawal_strength * 0.005)
            agent.emotion.sadness = min(
                1.0, agent.emotion.sadness + state.withdrawal_strength * 0.05
            )
            agent.emotion.joy = max(0.0, agent.emotion.joy - state.withdrawal_strength * 0.05)

        if state.is_dependent:
            agent.emotion.anticipation = min(1.0, agent.emotion.anticipation + 0.02)

            if np.random.random() < state.tolerance_level * 0.02:
                agent.emotion.trust = max(0.0, agent.emotion.trust - 0.01)

    def get_addiction_stats(self) -> Dict:
        dependent = sum(1 for s in self._addiction_states.values() if s.is_dependent)
        craving = sum(1 for s in self._addiction_states.values() if s.craving_intensity > 0.3)
        withdrawal = sum(1 for s in self._addiction_states.values() if s.withdrawal_strength > 0.2)

        return {
            "tracked": len(self._addiction_states),
            "dependent": dependent,
            "experiencing_craving": craving,
            "in_withdrawal": withdrawal,
            "avg_tolerance": np.mean([s.tolerance_level for s in self._addiction_states.values()])
            if self._addiction_states
            else 0.0,
        }
