from dataclasses import dataclass, field
from typing import Optional
from .types import TickContext, WorldEvent, EventType


@dataclass
class EnergySnapshot:
    tick: int
    grid_energy: float
    agent_energy: float
    total_energy: float
    changes: dict[str, float] = field(default_factory=dict)


class EnergyConservationValidator:
    def __init__(self, world):
        self.world = world
        self._initial_energy: Optional[float] = None
        self._snapshots: list[EnergySnapshot] = []
        self._tick_changes: dict[str, float] = {}
        self._violations: list[dict] = []
        self._enabled = True
        self._tolerance = 0.001

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.biology_tick and self._enabled

    def initialize(self):
        self._initial_energy = self._compute_energy()
        self._snapshots.append(
            EnergySnapshot(
                tick=self.world.tick,
                grid_energy=self._get_grid_energy(),
                agent_energy=self._get_agent_energy(),
                total_energy=self._initial_energy,
            )
        )

    def _compute_energy(self) -> float:
        return self.world.total_energy()

    def _get_grid_energy(self) -> float:
        return sum(
            sum(pool.values()) for cell in self.world.grid.values() for pool in [cell.chemical_pool]
        )

    def _get_agent_energy(self) -> float:
        return sum(a.energy for a in self.world.agents.values() if a.is_alive)

    def record_change(self, source: str, amount: float):
        if source not in self._tick_changes:
            self._tick_changes[source] = 0.0
        self._tick_changes[source] += amount

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        if self._initial_energy is None:
            self.initialize()
            return []

        current = self._compute_energy()
        expected = self._initial_energy + sum(self._tick_changes.values())
        difference = current - expected
        abs_difference = abs(difference)

        snapshot = EnergySnapshot(
            tick=self.world.tick,
            grid_energy=self._get_grid_energy(),
            agent_energy=self._get_agent_energy(),
            total_energy=current,
            changes=dict(self._tick_changes),
        )
        self._snapshots.append(snapshot)

        events = []
        if abs_difference > self._tolerance:
            violation = {
                "tick": self.world.tick,
                "current": current,
                "expected": expected,
                "difference": difference,
                "relative_error": abs_difference / max(abs(expected), 1e-10),
                "changes": dict(self._tick_changes),
            }
            self._violations.append(violation)
            events.append(
                WorldEvent(
                    tick=self.world.tick,
                    type=EventType.ENERGY_TRANSFER,
                    data=violation,
                    source_id="energy_validator",
                )
            )

        self._tick_changes.clear()
        return events

    def get_conservation_error(self) -> dict:
        if not self._snapshots:
            return {}

        latest = self._snapshots[-1]
        initial = self._snapshots[0]
        total_change = latest.total_energy - initial.total_energy

        return {
            "initial_energy": initial.total_energy,
            "current_energy": latest.total_energy,
            "absolute_change": total_change,
            "relative_error": abs(total_change) / max(abs(initial.total_energy), 1e-10),
            "violation_count": len(self._violations),
        }

    def get_violations(self) -> list[dict]:
        return self._violations

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False

    def reset(self):
        self._initial_energy = None
        self._snapshots.clear()
        self._tick_changes.clear()
        self._violations.clear()
