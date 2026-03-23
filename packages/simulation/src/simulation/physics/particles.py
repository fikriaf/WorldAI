import numpy as np
from ..systems.base import System
from ..types import TickContext, WorldEvent, Agent


class PhysicsSystem(System):
    def __init__(self, world):
        super().__init__(world)
        self._cache_positions: np.ndarray = None
        self._cache_masses: np.ndarray = None
        self._use_spatial = True

    def update(self, ctx: TickContext) -> list[WorldEvent]:
        if not ctx.physics_tick:
            return []

        agents = [a for a in self.world.agents.values() if a.is_alive]
        if not agents:
            return []

        from .optimized import compute_forces_fast, verlet_integrate, apply_boundary_conditions

        n = len(agents)
        positions = np.empty((n, 2), dtype=np.float64)
        velocities = np.empty((n, 2), dtype=np.float64)
        masses = np.empty(n, dtype=np.float64)

        for i, agent in enumerate(agents):
            positions[i, 0] = agent.position.x
            positions[i, 1] = agent.position.y
            velocities[i, 0] = agent.velocity.x
            velocities[i, 1] = agent.velocity.y
            masses[i] = agent.mass

        forces = compute_forces_fast(
            positions,
            masses,
            G=self.world.config.fundamental.G_digital,
            damping=0.01,
            cutoff=20.0,
            use_spatial=self._use_spatial,
            grid_size=5.0,
        )

        new_pos, new_vel = verlet_integrate(positions, velocities, forces, masses, ctx.dt)

        W = float(self.world.config.grid_width)
        H = float(self.world.config.grid_height)
        new_pos, new_vel = apply_boundary_conditions(new_pos, new_vel, W, H, bounce=0.5)

        for i, agent in enumerate(agents):
            agent.position.x = float(new_pos[i, 0])
            agent.position.y = float(new_pos[i, 1])
            agent.velocity.x = float(new_vel[i, 0])
            agent.velocity.y = float(new_vel[i, 1])

        if n > 50:
            self._use_spatial = True

        return []
