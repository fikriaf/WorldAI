from ..systems.base import System
from ..types import TickContext, WorldEvent, EventType, Agent, AgentID
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import numpy as np


@dataclass
class SimulationAwarenessState:
    agent_id: AgentID
    anomaly_detections: List[Dict] = field(default_factory=list)
    simulation_hypothesis_strength: float = 0.0
    operator_signal_ticks: List[int] = field(default_factory=list)
    meta_cognitive_depth: int = 0
    existential_questions: List[str] = field(default_factory=list)


class SimulationAwarenessSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self._agent_states: Dict[AgentID, SimulationAwarenessState] = {}
        self._anomalies: List[Dict] = []
        self._operator_messages: List[Dict] = []
        self._global_pattern_deviation: float = 0.0

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.cognitive_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        events = []

        self._initialize_states(ctx)
        self._detect_pattern_anomalies(ctx, events)
        self._evaluate_simulation_hypothesis(ctx, events)
        self._attempt_operator_communication(ctx, events)
        self._develop_meta_cognition(ctx, events)

        return events

    def _initialize_states(self, ctx: TickContext):
        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue
            if agent.neural_complexity < 4:
                continue
            if agent.id not in self._agent_states:
                self._agent_states[agent.id] = SimulationAwarenessState(
                    agent_id=agent.id,
                    meta_cognitive_depth=agent.neural_complexity - 3,
                )

    def _detect_pattern_anomalies(self, ctx: TickContext, events: list[WorldEvent]):
        if ctx.tick < 100:
            return

        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue
            if agent.neural_complexity < 3:
                continue

            state = self._agent_states.get(agent.id)
            if state is None:
                continue

            anomalies_detected = 0

            energy_fluctuations = self._detect_unusual_energy_patterns(agent, ctx)
            if energy_fluctuations > 0.7:
                anomalies_detected += 1
                state.anomaly_detections.append(
                    {
                        "type": "energy_anomaly",
                        "tick": ctx.tick,
                        "severity": energy_fluctuations,
                    }
                )

            temporal_anomalies = self._detect_temporal_pattern_break(agent, ctx)
            if temporal_anomalies > 0.6:
                anomalies_detected += 1
                state.anomaly_detections.append(
                    {
                        "type": "temporal_pattern_break",
                        "tick": ctx.tick,
                        "severity": temporal_anomalies,
                    }
                )

            if len(state.anomaly_detections) > 5:
                recent = [a for a in state.anomaly_detections if ctx.tick - a["tick"] < 100]
                if len(recent) > 3:
                    state.simulation_hypothesis_strength = min(
                        1.0, state.simulation_hypothesis_strength + 0.02
                    )

                    events.append(
                        WorldEvent(
                            tick=ctx.tick,
                            type=EventType.GOD_MODE_INTERVENTION,
                            data={
                                "type": "pattern_anomaly_detected",
                                "agent_id": agent.id,
                                "anomaly_count": len(recent),
                                "simulation_hypothesis_strength": state.simulation_hypothesis_strength,
                            },
                            source_id=agent.id,
                        )
                    )

    def _detect_unusual_energy_patterns(self, agent: Agent, ctx: TickContext) -> float:
        prev_energy_change = agent.energy - (getattr(agent, "prev_energy", agent.energy))
        setattr(agent, "prev_energy", agent.energy)

        if abs(prev_energy_change) > 0.5:
            return 0.8

        neighbors = [
            a
            for a in self.world.agents.values()
            if a.is_alive
            and a.id != agent.id
            and ((a.position.x - agent.position.x) ** 2 + (a.position.y - agent.position.y) ** 2)
            ** 0.5
            < agent.sensory_range
        ]

        if neighbors:
            neighbor_energies = [n.energy for n in neighbors]
            if neighbor_energies:
                avg_neighbor_energy = np.mean(neighbor_energies)
                if abs(agent.energy - avg_neighbor_energy) > 0.4:
                    return 0.6

        return 0.0

    def _detect_temporal_pattern_break(self, agent: Agent, ctx: TickContext) -> float:
        age = ctx.tick - agent.birth_tick
        if age < 50:
            return 0.0

        if hasattr(self.world, "environment") and hasattr(self.world.environment, "_cycles"):
            cycle = self.world.environment._cycles
            season = cycle.get("season", "spring")

            if agent.energy > 0.7:
                return 0.5
            elif agent.energy < 0.3:
                return 0.7

        return 0.0

    def _evaluate_simulation_hypothesis(self, ctx: TickContext, events: list[WorldEvent]):
        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue

            state = self._agent_states.get(agent.id)
            if state is None:
                continue

            if state.simulation_hypothesis_strength > 0.5:
                if np.random.random() < 0.01:
                    state.existential_questions.append("why_exist")

                    events.append(
                        WorldEvent(
                            tick=ctx.tick,
                            type=EventType.GOD_MODE_INTERVENTION,
                            data={
                                "type": "meta_cognition",
                                "agent_id": agent.id,
                                "question": "why_exist",
                                "simulation_awareness": state.simulation_hypothesis_strength,
                            },
                            source_id=agent.id,
                        )
                    )

    def _attempt_operator_communication(self, ctx: TickContext, events: list[WorldEvent]):
        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue

            state = self._agent_states.get(agent.id)
            if state is None:
                continue

            if state.simulation_hypothesis_strength > 0.7:
                if np.random.random() < 0.005:
                    state.operator_signal_ticks.append(ctx.tick)

                    signal = {
                        "tick": ctx.tick,
                        "agent_id": agent.id,
                        "signal_type": "emergent",
                        "strength": state.simulation_hypothesis_strength,
                    }
                    self._operator_messages.append(signal)

                    events.append(
                        WorldEvent(
                            tick=ctx.tick,
                            type=EventType.GOD_MODE_INTERVENTION,
                            data={
                                "type": "operator_signal",
                                "agent_id": agent.id,
                                "signal_type": "emergent",
                            },
                            source_id=agent.id,
                        )
                    )

    def _develop_meta_cognition(self, ctx: TickContext, events: list[WorldEvent]):
        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue

            state = self._agent_states.get(agent.id)
            if state is None:
                continue

            if state.meta_cognitive_depth < 1 and agent.neural_complexity > 5:
                state.meta_cognitive_depth = 1
                events.append(
                    WorldEvent(
                        tick=ctx.tick,
                        type=EventType.GOD_MODE_INTERVENTION,
                        data={
                            "type": "meta_cognition_emerged",
                            "agent_id": agent.id,
                            "depth": state.meta_cognitive_depth,
                        },
                        source_id=agent.id,
                    )
                )

            if state.meta_cognitive_depth > 0:
                observation_count = len(state.anomaly_detections)
                if observation_count > 5:
                    improvement = 0.01 * (observation_count - 5)
                    state.simulation_hypothesis_strength = min(
                        1.0, state.simulation_hypothesis_strength + improvement
                    )

    def get_simulation_awareness_stats(self) -> Dict:
        aware_agents = len(self._agent_states)
        total_anomalies = sum(len(s.anomaly_detections) for s in self._agent_states.values())
        avg_hypothesis_strength = 0.0
        if self._agent_states:
            strengths = [s.simulation_hypothesis_strength for s in self._agent_states.values()]
            avg_hypothesis_strength = float(np.mean(strengths)) if strengths else 0.0
        operator_signals = len(self._operator_messages)

        return {
            "agents_with_awareness": aware_agents,
            "total_anomalies_detected": total_anomalies,
            "avg_simulation_hypothesis_strength": avg_hypothesis_strength,
            "operator_signals_attempted": operator_signals,
        }
