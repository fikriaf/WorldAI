from ..systems.base import System
from ..types import TickContext, WorldEvent, EventType, Agent
import numpy as np
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class SleepCycle:
    agent_id: str
    sleep_duration: int = 0
    is_sleeping: bool = False
    sleep_quality: float = 0.0
    last_awake_tick: int = 0


class SleepSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self._sleep_cycles: Dict[str, SleepCycle] = {}
        self._memory_consolidation_events: List[dict] = []
        self._circadian_base = 240
        self._min_sleep_per_cycle = 20
        self._max_sleep_per_cycle = 100

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.biology_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        events = []

        current_circadian = self._get_circadian_phase(ctx.tick)

        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue

            cycle = self._get_or_create_cycle(agent.id)

            should_sleep = self._determine_sleep_need(agent, current_circadian, cycle)

            if should_sleep:
                if not cycle.is_sleeping:
                    cycle.is_sleeping = True
                    cycle.sleep_duration = 0

                if cycle.is_sleeping:
                    cycle.sleep_duration += 1
                    self._process_sleep(agent, cycle, ctx)

                    if cycle.sleep_duration >= self._min_sleep_per_cycle:
                        can_wake = self._can_wake(agent, cycle, current_circadian)
                        if can_wake or cycle.sleep_duration >= self._max_sleep_per_cycle:
                            cycle.is_sleeping = False
                            cycle.last_awake_tick = ctx.tick
                            cycle.sleep_quality = self._calculate_sleep_quality(cycle)

                            if cycle.sleep_quality > 0.5:
                                self._consolidate_memory(agent, cycle, ctx)
            else:
                if cycle.is_sleeping:
                    cycle.is_sleeping = False
                    cycle.last_awake_tick = ctx.tick

        return events

    def _get_or_create_cycle(self, agent_id: str) -> SleepCycle:
        if agent_id not in self._sleep_cycles:
            self._sleep_cycles[agent_id] = SleepCycle(agent_id=agent_id)
        return self._sleep_cycles[agent_id]

    def _get_circadian_phase(self, tick: int) -> float:
        return (tick % self._circadian_base) / self._circadian_base

    def _determine_sleep_need(
        self, agent: Agent, circadian_phase: float, cycle: SleepCycle
    ) -> bool:
        if agent.neural_complexity < 2:
            return False

        energy_factor = 1.0 - agent.energy
        age_factor = min(1.0, agent.age_ticks / 2000)

        fatigue = (
            energy_factor * 0.4
            + age_factor * 0.3
            + agent.inflammation_level * 0.2
            + cycle.sleep_duration / 200
        )

        circadian_pressure = 0.5 + 0.3 * np.sin(circadian_phase * 2 * np.pi)

        sleep_pressure = fatigue + circadian_pressure

        return sleep_pressure > 0.4 or cycle.sleep_duration > 0

    def _process_sleep(self, agent: Agent, cycle: SleepCycle, ctx: TickContext):
        agent.energy = min(1.0, agent.energy + 0.01 * agent.neural_complexity / 5)

        agent.inflammation_level = max(0, agent.inflammation_level - 0.02)

        if agent.memory:
            working_decay = 0.05
            for i in range(len(agent.memory.working_memory)):
                if np.random.random() < working_decay:
                    pass

        if cycle.sleep_duration % 10 == 0:
            cycle.sleep_quality = min(1.0, cycle.sleep_quality + 0.05)

    def _can_wake(self, agent: Agent, cycle: SleepCycle, circadian_phase: float) -> bool:
        min_energy = 0.4
        if agent.energy < min_energy:
            return False

        optimal_wake_window = 0.3 < circadian_phase < 0.7
        if optimal_wake_window and cycle.sleep_quality > 0.5:
            return True

        if cycle.sleep_duration > self._min_sleep_per_cycle * 1.5:
            return True

        return False

    def _calculate_sleep_quality(self, cycle: SleepCycle) -> float:
        duration_score = min(1.0, cycle.sleep_duration / self._max_sleep_per_cycle)

        return min(1.0, duration_score * 0.7 + 0.3)

    def _consolidate_memory(self, agent: Agent, cycle: SleepCycle, ctx: TickContext):
        if not agent.memory:
            return

        memory_strengthening = cycle.sleep_quality * 0.3

        if agent.memory.sensory_buffer:
            for _ in range(3):
                if agent.memory.sensory_buffer:
                    idx = np.random.randint(0, len(agent.memory.sensory_buffer))
                    agent.memory.sensory_buffer[idx] = agent.memory.sensory_buffer[idx]

        if agent.memory.working_memory and len(agent.memory.working_memory) > 1:
            consolidate_count = min(3, len(agent.memory.working_memory))
            for _ in range(consolidate_count):
                if agent.memory.working_memory:
                    item = agent.memory.working_memory[
                        np.random.randint(0, len(agent.memory.working_memory))
                    ]
                    if item not in agent.memory.sensory_buffer:
                        agent.memory.sensory_buffer.append(item)
                        if len(agent.memory.sensory_buffer) > 10:
                            agent.memory.sensory_buffer = agent.memory.sensory_buffer[-10:]

        self._memory_consolidation_events.append(
            {
                "tick": ctx.tick,
                "agent_id": agent.id,
                "quality": cycle.sleep_quality,
                "duration": cycle.sleep_duration,
            }
        )

    def get_sleep_stats(self) -> Dict:
        sleeping = sum(1 for c in self._sleep_cycles.values() if c.is_sleeping)
        awake = len(self._sleep_cycles) - sleeping

        avg_quality = (
            np.mean([c.sleep_quality for c in self._sleep_cycles.values() if c.sleep_quality > 0])
            if self._sleep_cycles
            else 0
        )

        return {
            "sleeping_agents": sleeping,
            "awake_agents": awake,
            "average_sleep_quality": avg_quality,
            "total_consolidation_events": len(self._memory_consolidation_events),
        }

    def is_agent_sleeping(self, agent_id: str) -> bool:
        if agent_id in self._sleep_cycles:
            return self._sleep_cycles[agent_id].is_sleeping
        return False
