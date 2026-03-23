import numpy as np
from ..systems.base import System
from ..types import TickContext, WorldEvent, EventType, GridCell


class ThermodynamicsSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self._temperature_history: list[float] = []
        self._entropy_history: list[float] = []
        self._heat_capacity = 1.0
        self._thermal_conductivity = 0.05
        self._solar_input = 1.0

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.physics_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        events = []

        self._process_solar_input()
        self._diffuse_temperature()
        self._calculate_entropy()

        if ctx.tick % 100 == 0 and self.world.energy_validator:
            avg_temp = self._get_average_temperature()
            entropy = self._calculate_system_entropy()
            self._temperature_history.append(avg_temp)
            self._entropy_history.append(entropy)

            self.world.energy_validator.record_change("thermodynamics", 0.0)

        return events

    def _process_solar_input(self):
        day_cycle = (self.world.tick % 240) / 240.0
        sunlight = max(0.0, np.sin(day_cycle * np.pi) * self._solar_input)

        for cell in self.world.grid.values():
            cell.temperature += sunlight * 0.1
            cell.temperature = max(0.0, min(100.0, cell.temperature))

    def _diffuse_temperature(self):
        grid = self.world.grid
        width = self.world.config.grid_width
        height = self.world.config.grid_height
        k = self._thermal_conductivity

        new_temps = {}
        for (x, y), cell in grid.items():
            neighbors = []
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = (x + dx) % width, (y + dy) % height
                if (nx, ny) in grid:
                    neighbors.append(grid[(nx, ny)].temperature)

            if neighbors:
                avg_neighbor = sum(neighbors) / len(neighbors)
                new_temp = cell.temperature + k * (avg_neighbor - cell.temperature)
                new_temps[(x, y)] = max(0.0, min(100.0, new_temp))

        for (x, y), temp in new_temps.items():
            grid[(x, y)].temperature = temp

    def _calculate_entropy(self) -> float:
        return self._calculate_system_entropy()

    def _calculate_system_entropy(self) -> float:
        total_entropy = 0.0
        k_B = 1.0

        temps = [c.temperature for c in self.world.grid.values() if c.temperature > 0]
        if not temps:
            return 0.0

        avg_temp = sum(temps) / len(temps)

        for cell in self.world.grid.values():
            if cell.temperature > 0:
                energy = cell.temperature * self._heat_capacity
                if energy > 0:
                    entropy = k_B * np.log(energy / (cell.temperature + 1e-10))
                    total_entropy += max(0, entropy)

        return total_entropy

    def _get_average_temperature(self) -> float:
        temps = [c.temperature for c in self.world.grid.values()]
        return sum(temps) / len(temps) if temps else 20.0

    def get_temperature_range(self) -> tuple[float, float]:
        if not self.world.grid:
            return (20.0, 20.0)

        temps = [c.temperature for c in self.world.grid.values()]
        return (min(temps), max(temps))

    def get_thermal_energy(self) -> float:
        return sum(c.temperature * self._heat_capacity for c in self.world.grid.values())

    def get_entropy_history(self) -> list[float]:
        return self._entropy_history.copy()

    def get_temperature_history(self) -> list[float]:
        return self._temperature_history.copy()
