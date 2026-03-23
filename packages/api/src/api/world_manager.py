import asyncio
import json
import uuid
from typing import Optional
from datetime import datetime


class WorldManager:
    def __init__(self):
        self.world: Optional[object] = None
        self.world_id: Optional[str] = None
        self.running: bool = False
        self._task: Optional[asyncio.Task] = None
        self._events: list = []
        self._stats = {
            "births": 0,
            "deaths": 0,
            "chemistry_events": 0,
        }
        self._redis_enabled = False
        self._redis = None

    def _init_redis(self):
        try:
            from .redis_state import get_state_manager

            self._redis = get_state_manager()
            self._redis_enabled = self._redis.is_connected()
            if self._redis_enabled:
                print("Redis connected for state persistence")
        except Exception as e:
            print(f"Redis not available: {e}")
            self._redis_enabled = False

    async def create_world(
        self,
        seed_id: str = "default",
        grid_width: int = 64,
        grid_height: int = 64,
        genesis_mode: str = "seeded_chemistry",
        observer_enabled: bool = False,
    ) -> str:
        if self.world is not None:
            await self.stop_world()

        if not self._redis:
            self._init_redis()

        from simulation import World, SimulationConfig
        from simulation.types import (
            SimulationConfig,
            FundamentalConstants,
            ChemicalConfig,
            EnvironmentalConfig,
        )

        config = SimulationConfig(
            seed_id=seed_id,
            genesis_mode=genesis_mode,
            grid_width=grid_width,
            grid_height=grid_height,
            initial_energy_density=1.0,
        )

        self.world = World(config, observer_enabled=observer_enabled)
        self.world_id = str(uuid.uuid4())[:8]
        self.running = True
        self._stats = {"births": 0, "deaths": 0, "chemistry_events": 0}
        self._events = []

        if self._redis_enabled:
            self._redis.clear_all()

        return self.world_id

    async def stop_world(self):
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        if self._redis_enabled and self.world:
            self._persist_state()

        self.world = None
        self.world_id = None

    def _persist_state(self):
        if not self._redis_enabled or not self.world:
            return

        state = {
            "world_id": self.world_id,
            "tick": self.world.tick,
            "population": len(self.world.agents),
            "total_energy": self.world.total_energy(),
            "stats": self._stats,
        }
        self._redis.save_world_state(state)

    async def step(self) -> dict:
        if self.world is None:
            return {"error": "World not running"}

        events = self.world.step()

        for event in events:
            event_dict = {
                "tick": event.tick,
                "type": event.type.value,
                "data": event.data,
                "timestamp": datetime.utcnow().isoformat(),
            }
            self._events.append(event_dict)

            if self._redis_enabled:
                self._redis.save_event(event_dict)

            if event.type.value == "agent_born":
                self._stats["births"] += 1
            elif event.type.value == "agent_died":
                self._stats["deaths"] += 1
            elif event.type.value == "chemical_reaction":
                self._stats["chemistry_events"] += 1

        if len(self._events) > 1000:
            self._events = self._events[-500:]

        if self._redis_enabled and self.world.tick % 10 == 0:
            self._persist_state()

            if self._redis_enabled:
                state = await self.get_state()
                if state:
                    self._redis.publish_state(state)

        return {
            "tick": self.world.tick,
            "events": len(events),
            "population": len(self.world.agents),
        }

    async def run(self, ticks: int = 100) -> dict:
        if self.world is None:
            return {"error": "World not running"}

        for _ in range(ticks):
            await self.step()
            if not self.running:
                break

        return {
            "ticks_run": ticks,
            "current_tick": self.world.tick,
            "population": len(self.world.agents),
        }

    async def get_state(self) -> Optional[dict]:
        if self.world is None:
            if self._redis_enabled:
                return self._redis.load_world_state()
            return None

        agents = []
        for agent in self.world.agents.values():
            agents.append(
                {
                    "id": agent.id,
                    "position_x": agent.position.x,
                    "position_y": agent.position.y,
                    "velocity_x": agent.velocity.x,
                    "velocity_y": agent.velocity.y,
                    "energy": agent.energy,
                    "health": agent.health,
                    "age_ticks": agent.age_ticks,
                    "stage": agent.stage.value,
                    "genome_hash": agent.genome.checksum(),
                    "genes_count": len(agent.genome.genes),
                    "species_label": getattr(agent, "species_label", None),
                    "parent_count": len(agent.parent_ids),
                    "children_count": len(agent.children_ids),
                }
            )

        grid_data = []
        for (x, y), cell in self.world.grid.items():
            grid_data.append(
                {
                    "x": x,
                    "y": y,
                    "chemical_pool": dict(cell.chemical_pool),
                    "temperature": cell.temperature,
                    "light_level": cell.light_level,
                    "rd_u": cell.rd.u,
                    "rd_v": cell.rd.v,
                }
            )

        return {
            "world_id": self.world_id,
            "tick": self.world.tick,
            "population": len(agents),
            "total_energy": self.world.total_energy(),
            "agents": agents[:100],
            "grid_data": grid_data,
            "recent_events": self._events[-20:],
            "stats": dict(self._stats),
        }

    async def get_stats(self) -> Optional[dict]:
        if self.world is None:
            return None

        return {
            "tick": self.world.tick,
            "population": len(self.world.agents),
            "births_total": self._stats["births"],
            "deaths_total": self._stats["deaths"],
            "chemistry_events": self._stats["chemistry_events"],
            "total_energy": self.world.total_energy(),
            "redis_enabled": self._redis_enabled,
        }

    async def get_agent(self, agent_id: str) -> Optional[dict]:
        if self.world is None:
            return None

        agent = self.world.agents.get(agent_id)
        if agent is None:
            return None

        return {
            "id": agent.id,
            "position": {"x": agent.position.x, "y": agent.position.y},
            "velocity": {"x": agent.velocity.x, "y": agent.velocity.y},
            "energy": agent.energy,
            "health": agent.health,
            "age_ticks": agent.age_ticks,
            "stage": agent.stage.value,
            "genome_hash": agent.genome.checksum(),
            "genes_count": len(agent.genome.genes),
            "parent_ids": agent.parent_ids,
            "children_ids": agent.children_ids,
            "species_label": getattr(agent, "species_label", None),
            "emotion": {
                "fear": agent.emotion.fear,
                "anger": agent.emotion.anger,
                "joy": agent.emotion.joy,
            },
        }

    async def get_recent_events(self, limit: int = 50) -> list:
        if self._redis_enabled:
            return self._redis.get_recent_events(limit)
        return self._events[-limit:]

    async def get_metrics_history(self, limit: int = 100) -> list:
        if self._redis_enabled:
            return self._redis.get_metrics_history(limit)
        return []


world_manager = WorldManager()
