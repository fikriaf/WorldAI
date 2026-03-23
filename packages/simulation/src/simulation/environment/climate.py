from ..systems.base import System
from ..types import TickContext, WorldEvent, EventType, ElementType
from dataclasses import dataclass
import math


@dataclass
class ClimateState:
    temperature: float
    humidity: float
    pressure: float
    wind_x: float
    wind_y: float
    disaster_pending: bool = False
    disaster_type: str = "none"
    disaster_severity: float = 0.0


class ClimateSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self.climate_state = ClimateState(
            temperature=20.0,
            humidity=0.5,
            pressure=1.0,
            wind_x=0.0,
            wind_y=0.0,
        )
        self._disaster_cooldown = 0
        self._tectonic_tick = 0

    def should_run(self, ctx: TickContext) -> bool:
        return ctx.geological_tick

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        events = []
        if self._disaster_cooldown > 0:
            self._disaster_cooldown -= 1

        self._update_temperature(ctx)
        self._update_humidity(ctx)
        self._update_pressure(ctx)
        self._update_wind(ctx)
        self._apply_climate_to_grid()

        if self._disaster_cooldown == 0:
            disaster = self._check_disaster(ctx)
            if disaster:
                events.extend(disaster)
                self._disaster_cooldown = 500

        return events

    def _update_temperature(self, ctx: TickContext):
        base = 20.0
        latitude_effect = 0.0
        for (x, y), cell in list(self.world.grid.items())[:10]:
            latitude_effect += (y / self.world.config.grid_height - 0.5) * 10
        latitude_effect /= 10.0

        solar_cycle = math.sin(2 * math.pi * ctx.tick / 1000) * 5
        volatility = self.world.config.environmental.climate_volatility
        noise = (math.sin(ctx.tick * 0.1) + math.cos(ctx.tick * 0.07)) * volatility * 3

        self.climate_state.temperature = base + latitude_effect + solar_cycle + noise
        self.climate_state.temperature = max(-50, min(60, self.climate_state.temperature))

    def _update_humidity(self, ctx: TickContext):
        base_humidity = 0.5
        temp_factor = (self.climate_state.temperature - 20) / 40
        evaporation = max(0, -temp_factor * 0.1)
        precipitation = max(0, temp_factor * 0.05)
        noise = math.sin(ctx.tick * 0.05) * 0.02

        self.climate_state.humidity = max(
            0.0, min(1.0, base_humidity - evaporation + precipitation + noise)
        )

    def _update_pressure(self, ctx: TickContext):
        base = 1.0
        latitude = 0.5
        for (x, y), cell in self.world.grid.items():
            latitude = y / self.world.config.grid_height
            break

        pressure_gradient = (latitude - 0.5) * 0.1
        noise = math.sin(ctx.tick * 0.03) * 0.02
        self.climate_state.pressure = max(0.5, min(1.5, base + pressure_gradient + noise))

    def _update_wind(self, ctx: TickContext):
        pressure = self.climate_state.pressure
        humidity = self.climate_state.humidity
        dx = (0.5 - pressure) * 2 + (humidity - 0.5) * 0.5
        dy = math.sin(ctx.tick * 0.02) * 0.1

        self.climate_state.wind_x = self.climate_state.wind_x * 0.9 + dx * 0.1
        self.climate_state.wind_y = self.climate_state.wind_y * 0.9 + dy * 0.1

        max_wind = 2.0
        mag = math.sqrt(self.climate_state.wind_x**2 + self.climate_state.wind_y**2)
        if mag > max_wind:
            self.climate_state.wind_x = (self.climate_state.wind_x / mag) * max_wind
            self.climate_state.wind_y = (self.climate_state.wind_y / mag) * max_wind

    def _apply_climate_to_grid(self):
        temp = self.climate_state.temperature
        wind_x = self.climate_state.wind_x
        wind_y = self.climate_state.wind_y

        for cell in self.world.grid.values():
            cell.temperature = max(-50, min(60, temp + (hash((cell.x, cell.y)) % 100 - 50) * 0.1))

            cell.light_level = max(
                0.0,
                min(1.0, 0.5 + math.sin(cell.y / self.world.config.grid_height * math.pi) * 0.3),
            )

            cell.chemical_pool[ElementType.IGNIS] = (
                max(0.0, temp / 60.0 * 2.0) if hasattr(self, "world") else 0.0
            )

    def _check_disaster(self, ctx: TickContext) -> list[WorldEvent]:
        import random

        events = []

        base_prob = self.world.config.environmental.disaster_base_probability
        volatility = self.world.config.environmental.climate_volatility
        prob = base_prob * (1.0 + volatility)

        if random.random() > prob:
            return events

        disaster_types = ["drought", "flood", "fire", "storm", "earthquake"]
        weights = [0.3, 0.25, 0.2, 0.15, 0.1]

        disaster = random.choices(disaster_types, weights=weights, k=1)[0]
        severity = random.uniform(0.3, 1.0)

        self.climate_state.disaster_pending = True
        self.climate_state.disaster_type = disaster
        self.climate_state.disaster_severity = severity

        affected_agents = 0
        for agent in self.world.agents.values():
            if not agent.is_alive:
                continue
            cell_x = int(agent.position.x) % self.world.config.grid_width
            cell_y = int(agent.position.y) % self.world.config.grid_height
            cell = self.world.grid.get((cell_x, cell_y))
            if not cell:
                continue

            if disaster == "drought":
                agent.energy -= severity * 0.2
                cell.chemical_pool[ElementType.AQUA] *= 1.0 - severity * 0.3
            elif disaster == "flood":
                agent.energy -= severity * 0.15
                cell.chemical_pool[ElementType.AQUA] *= 1.0 + severity * 0.5
            elif disaster == "fire":
                agent.energy -= severity * 0.3
                agent.health -= severity * 0.2
            elif disaster == "storm":
                dx = agent.position.x - self.world.config.grid_width / 2
                dy = agent.position.y - self.world.config.grid_height / 2
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < self.world.config.grid_width / 3:
                    agent.velocity.x += wind_x * severity * 0.5
                    agent.velocity.y += wind_y * severity * 0.5
                    agent.energy -= severity * 0.1
            elif disaster == "earthquake":
                if random.random() < severity * 0.5:
                    agent.energy -= severity * 0.25
                    agent.position.x += random.uniform(-1, 1) * severity
                    agent.position.y += random.uniform(-1, 1) * severity

            affected_agents += 1

        events.append(
            WorldEvent(
                tick=ctx.tick,
                type=EventType.GOD_MODE_INTERVENTION,
                data={
                    "type": "disaster",
                    "disaster_type": disaster,
                    "severity": severity,
                    "affected_agents": affected_agents,
                },
                source_id="climate_system",
            )
        )

        self.climate_state.disaster_pending = False
        return events

    def get_climate_summary(self) -> dict:
        return {
            "temperature": self.climate_state.temperature,
            "humidity": self.climate_state.humidity,
            "pressure": self.climate_state.pressure,
            "wind": (self.climate_state.wind_x, self.climate_state.wind_y),
            "disaster_cooldown": self._disaster_cooldown,
        }
