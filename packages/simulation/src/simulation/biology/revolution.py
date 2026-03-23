from ..systems.base import System
from ..types import TickContext, WorldEvent, EventType, Agent
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class RevolutionState:
    agent_id: str
    grievance_level: float = 0.0
    grievance_history: List[float] = field(default_factory=list)
    relative_deprivation: float = 0.0
    revolution_readiness: float = 0.0
    mobilization_count: int = 0


class RevolutionSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self._revolution_states: Dict[str, RevolutionState] = {}
        self._j_curve_threshold = 0.6
        self._tipping_point = 0.8

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.social_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        events = []

        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue

            state = self._get_or_create_state(agent)
            self._update_tocqueville_paradox(agent, state, ctx)
            self._compute_j_curve_dynamics(agent, state, ctx)
            self._check_tipping_points(agent, state, ctx, events)
            self._revolutionary_mobilization(agent, state, ctx, events)

        return events

    def _get_or_create_state(self, agent: Agent) -> RevolutionState:
        if agent.id not in self._revolution_states:
            self._revolution_states[agent.id] = RevolutionState(agent_id=agent.id)
        return self._revolution_states[agent.id]

    def _update_tocqueville_paradox(self, agent: Agent, state: RevolutionState, ctx: TickContext):
        current_conditions = self._assess_conditions(agent)
        expected_conditions = self._assess_expectations(agent)

        state.relative_deprivation = current_conditions - expected_conditions
        state.grievance_level = max(0, state.relative_deprivation)

        if len(state.grievance_history) > 20:
            state.grievance_history.pop(0)

        state.grievance_history.append(
            state.grievance_history[-1] if state.grievance_history else 0
        )

        if len(state.grievance_history) >= 10:
            recent_avg = np.mean(state.grievance_history[-10:])
            if current_conditions > recent_avg and recent_avg < self._j_curve_threshold:
                state.grievance_level = min(1.0, state.grievance_level + 0.1)

    def _assess_conditions(self, agent: Agent) -> float:
        health = agent.health
        energy = agent.energy
        wealth = getattr(agent, "economy_wealth", 0.5)
        group_size = 1
        if agent.group_id:
            group_size = sum(
                1 for a in self.world.agents.values() if a.group_id == agent.group_id and a.is_alive
            )

        conditions = health * 0.3 + energy * 0.3 + wealth * 0.2 + min(1.0, group_size / 10) * 0.2
        return conditions

    def _assess_expectations(self, agent: Agent) -> float:
        expectations = 0.5

        if agent.group_id:
            group_members = [
                a for a in self.world.agents.values() if a.group_id == agent.group_id and a.is_alive
            ]
            if group_members:
                group_avg_wealth = np.mean(
                    [getattr(a, "economy_wealth", 0.5) for a in group_members]
                )
                expectations = max(expectations, group_avg_wealth)

        if agent.neural_complexity > 3:
            expectations += 0.1

        return min(1.0, expectations)

    def _compute_j_curve_dynamics(self, agent: Agent, state: RevolutionState, ctx: TickContext):
        current_conditions = self._assess_conditions(agent)

        if len(state.grievance_history) > 1:
            improvement_rate = current_conditions - state.grievance_history[0]
        else:
            improvement_rate = 0

        if improvement_rate > 0:
            state.revolution_readiness = min(
                1.0, state.revolution_readiness + improvement_rate * 0.1
            )
        else:
            state.revolution_readiness = max(
                0, state.revolution_readiness - abs(improvement_rate) * 0.05
            )

        if state.grievance_history:
            variance = (
                np.var(state.grievance_history[-5:]) if len(state.grievance_history) >= 5 else 0
            )
            if variance > 0.1:
                state.revolution_readiness = min(1.0, state.revolution_readiness + 0.05)

    def _check_tipping_points(
        self, agent: Agent, state: RevolutionState, ctx: TickContext, events: List[WorldEvent]
    ):
        if state.revolution_readiness > self._tipping_point:
            phase = self._detect_phase_transition(state)
            if phase:
                events.append(
                    WorldEvent(
                        tick=ctx.tick,
                        type=EventType.GOD_MODE_INTERVENTION,
                        data={"revolution_phase": phase, "grievance": state.grievance_level},
                        source_id=agent.id,
                    )
                )

    def _detect_phase_transition(self, state: RevolutionState) -> str:
        if state.mobilization_count > 10:
            return "civil_war"
        elif state.mobilization_count > 5:
            return "armed_conflict"
        elif state.revolution_readiness > 0.9:
            return "revolutionary"
        elif state.revolution_readiness > 0.8:
            return "mobilization"
        return None

    def _revolutionary_mobilization(
        self, agent: Agent, state: RevolutionState, ctx: TickContext, events: List[WorldEvent]
    ):
        if state.grievance_level < 0.5:
            return

        if not agent.group_id:
            return

        group_members = [
            a for a in self.world.agents.values() if a.group_id == agent.group_id and a.is_alive
        ]

        grievances = [
            self._revolution_states[a.id].grievance_level
            for a in group_members
            if a.id in self._revolution_states
        ]

        if not grievances:
            return

        group_grievance = np.mean(grievances)

        if group_grievance > 0.6 and np.random.random() < group_grievance * 0.01:
            state.mobilization_count += 1

            agent.emotion.anger = min(1.0, agent.emotion.anger + 0.2)
            agent.emotion.fear = min(1.0, agent.emotion.fear + 0.1)

    def get_revolution_stats(self) -> Dict:
        if not self._revolution_states:
            return {"total_tracked": 0}

        avg_grievance = np.mean([s.grievance_level for s in self._revolution_states.values()])
        avg_readiness = np.mean([s.revolution_readiness for s in self._revolution_states.values()])

        return {
            "total_tracked": len(self._revolution_states),
            "avg_grievance": avg_grievance,
            "avg_revolution_readiness": avg_readiness,
            "total_mobilizations": sum(
                s.mobilization_count for s in self._revolution_states.values()
            ),
        }
